"""Stateful advisory mode: run this twice a day (morning/evening) instead of watching
charts continuously. Persists a small JSON position state per (symbol, market, strategy)
so the next check remembers what you're holding.

Sizing math is shared with the backtest engine via `compute_entry_allocation` so a fix
made there (e.g. the Kelly-lockout floor) automatically applies here too.

Timing note: the backtest engine shifts signals one bar forward (decide at close(T),
act at open(T+1)) because it's replaying history where "tomorrow" already happened. Live,
there's no future bar to wait for — this advisor uses the most recently available bar's
signal directly as the recommendation for your next action. Every report prints the as-of
date of the price data it used, so you can judge whether that's a completed session close
or a still-forming one (this tool has no broker connection and doesn't know market hours).

This is a decision-support tool, not an execution engine: it assumes you actually placed
the trade it last recommended. If you didn't, use --reset or edit the state file.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import NamedTuple

import pandas as pd
import yfinance as yf

from .config import (
    DEFAULT_CAPITAL,
    DEFAULT_COMMISSION_PCT,
    DEFAULT_RISK_PCT,
    DEFAULT_SIZE_PCT,
    DEFAULT_SIZING_MODE,
    DEFAULT_SLIPPAGE_PCT,
)
from .data import fetch_ohlcv, normalize_ticker
from .engine import compute_entry_allocation
from .strategy import STRATEGIES
from .trade_store import record_entry, record_trade

# Overridable via env so a cron deployment (e.g. Railway, ephemeral container filesystem)
# can point this at a mounted volume — otherwise state would reset to defaults every run.
STATE_DIR = Path(os.environ.get("BACKTESTER_STATE_DIR", str(Path(__file__).resolve().parent.parent / ".state")))

# Rule-of-thumb minimum tradable size per market — actual minimums vary by broker/exchange,
# these are typical retail defaults, not a guarantee. Confirm with your own broker.
_MIN_UNITS = {"forex": 1000, "us": 1, "set": 100}  # forex: micro lot; us: 1 share; set: 1 board lot
_MIN_NOTIONAL_CRYPTO = 10.0  # crypto exchanges mostly allow fractional units, minimum is usually a $ floor


def estimate_min_capital(market: str, price: float, stop_pct: float, risk_pct: float) -> tuple[float, float]:
    """Returns (min_notional, min_capital). min_notional is the $ value of the smallest
    trade this market typically allows; min_capital is how much account capital you'd
    need so that risking `risk_pct` of it still covers at least that minimum trade's stop
    distance — i.e. the smallest account size where "fractional" sizing stays meaningful.
    """
    if market == "crypto":
        min_notional = _MIN_NOTIONAL_CRYPTO
    else:
        min_notional = _MIN_UNITS[market] * price

    min_capital = min_notional * stop_pct / risk_pct if risk_pct > 0 else float("inf")
    return min_notional, min_capital


class AdviseResult(NamedTuple):
    report: str
    event: bool  # True only when a real entry/exit happened this call — not on HOLD/WAIT
    is_entry: bool = False  # True only for a fresh ENTER this call
    is_exit: bool = False  # True only for a fresh EXIT this call (stop/target/signal)
    # is_entry/is_exit both drive the same urgent-delivery treatment in cloud_run.py
    # (individual message + @mention + quick-confirm reaction prompt) — both are real
    # decision windows for anyone holding a matching real position, not just entries.


# Binance's web trade-page URL for a given pair is a stable, documented part of their site
# routing (not a special API) — unlike an actual pre-filled-order deep link, which neither
# Binance nor MT4/MT5 (Exness) expose publicly as of 2026-08-17 (checked before building
# this). This only saves a navigation tap; the human still places the real order themselves
# on the broker's own app, which is the point — this tool never touches a broker API key.
def _quick_action_link(symbol: str, market: str) -> str | None:
    if market == "crypto":
        return f"https://www.binance.com/en/trade/{symbol}_USDT?type=spot"
    return None


# Threshold above which the live price has moved far enough from the signal's reference
# price to be worth flagging explicitly, rather than trusting the reader to notice.
_STALE_PRICE_THRESHOLD_PCT = 1.5


def _live_price_deviation_warning(symbol: str, market: str, reference_price: float) -> str | None:
    """Best-effort staleness check: by the time a signal is read and acted on, the real
    price may already have moved (added 2026-08-17 after a "missing the trade window"
    report — yfinance's fast_info is a lightweight near-real-time quote, distinct from the
    daily-bar OHLCV history advise() otherwise uses). Never blocks or delays the signal
    itself — a fetch failure here just means no staleness line gets appended, not that the
    entry recommendation is withheld.
    """
    try:
        ticker = normalize_ticker(symbol, market)
        live_price = float(yf.Ticker(ticker).fast_info.last_price)
    except Exception as e:
        # Logged (not just silently swallowed) — this check failing 100% of the time in
        # production with nothing ever printed would be indistinguishable from it working
        # correctly and just never crossing the threshold. Found that gap 2026-08-21 while
        # investigating a "missing the trade window" report and being unable to tell from
        # logs alone whether staleness checks were even running.
        print(f"advisor: live-price staleness check failed for {symbol} ({market}): {e}", file=sys.stderr)
        return None
    print(f"advisor: live-price check for {symbol} — live={live_price:.5f} reference={reference_price:.5f}", file=sys.stderr)
    deviation_pct = (live_price / reference_price - 1) * 100
    if abs(deviation_pct) < _STALE_PRICE_THRESHOLD_PCT:
        return None
    return f"    ⚠️ ราคาล่าสุดตอนนี้ {live_price:.5f} (ห่างจากราคาที่สัญญาณคำนวณไว้ {deviation_pct:+.2f}%) — เช็คก่อนว่ายังน่าเข้าไหม"


def _state_path(symbol: str, market: str, strategy: str) -> Path:
    ticker = normalize_ticker(symbol, market).replace("/", "_")
    return STATE_DIR / f"{ticker}_{strategy}.json"


def _default_state(capital: float) -> dict:
    return {
        "cash": capital,
        "initial_capital": capital,
        "in_position": False,
        "entry_date": None,
        "entry_price": None,
        "shares": 0.0,
        "cost_basis": 0.0,
        "stop_level": None,
        "target_level": None,
        "trade_log": [],
    }


def load_state(path: Path, capital: float) -> dict:
    """Starts from defaults and overlays whatever's on disk, so a state file missing keys
    (hand-edited, or written by an older version of this tool) can't crash with KeyError."""
    state = _default_state(capital)
    if path.exists():
        with open(path) as f:
            state.update(json.load(f))
    return state


def is_in_position(symbol: str, market: str, strategy_name: str, capital: float) -> bool:
    """Quick state check without running a full advise() pass — used by cloud_run.py's
    correlation guard to count currently-open positions per market before deciding
    whether a new entry is allowed."""
    path = _state_path(symbol, market, strategy_name)
    state = load_state(path, capital)
    return bool(state.get("in_position"))


def save_state(path: Path, state: dict) -> None:
    """Writes via a temp file + atomic rename so an interrupted write can't leave a
    truncated/corrupt state file behind."""
    STATE_DIR.mkdir(exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w") as f:
        json.dump(state, f, indent=2, default=str)
    tmp_path.replace(path)


def advise(
    symbol: str,
    market: str,
    strategy_name: str,
    params: dict,
    capital: float = DEFAULT_CAPITAL,
    commission_pct: float = DEFAULT_COMMISSION_PCT,
    slippage_pct: float = DEFAULT_SLIPPAGE_PCT,
    sizing_mode: str = DEFAULT_SIZING_MODE,
    size_pct: float = DEFAULT_SIZE_PCT,
    risk_pct: float = DEFAULT_RISK_PCT,
    stop_pct: float | None = None,
    target_pct: float | None = None,
    reset: bool = False,
    lookback_days: int = 500,
    allow_entry: bool = True,
) -> AdviseResult:
    path = _state_path(symbol, market, strategy_name)
    if reset and path.exists():
        path.unlink()
    state = load_state(path, capital)

    start = (pd.Timestamp.today() - pd.Timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    df = fetch_ohlcv(symbol, market, start, None)

    strategy_fn = STRATEGIES[strategy_name]
    signal = strategy_fn(df, **params)

    latest_row = df.iloc[-1]
    latest_close = float(latest_row["Close"])
    latest_low = float(latest_row["Low"])
    latest_high = float(latest_row["High"])
    as_of = df.index[-1].strftime("%Y-%m-%d")
    signal_now = int(signal.iloc[-1])

    lines = [
        f"{symbol} ({market}) — {strategy_name}  |  ข้อมูลล่าสุด ณ {as_of} (Close={latest_close:.5f})",
        "-" * 60,
    ]

    event = False  # flips True only on a real entry/exit this call — drives Discord notify-on-change
    is_entry = False
    is_exit = False
    just_exited = False
    if state["in_position"]:
        stop_level = state["stop_level"]
        target_level = state["target_level"]
        exit_reason = None
        exit_price = None

        # Guard against checking the entry day's stop/target with its full-day High/Low,
        # which would include pre-entry intrabar action from before the position existed
        # (the backtest engine has the same protection: a stop can't fire on the entry bar).
        entered_today = state["entry_date"] == as_of

        # Same precedence as the backtest engine: a resting stop/target can fire off this
        # bar's intrabar range even before the strategy's own signal flips to flat.
        if not entered_today and stop_level is not None and latest_low <= stop_level:
            exit_reason, exit_price = "stop", stop_level
        elif not entered_today and target_level is not None and latest_high >= target_level:
            exit_reason, exit_price = "target", target_level
        elif signal_now == 0:
            exit_reason, exit_price = "signal", latest_close * (1 - slippage_pct)

        if exit_reason:
            just_exited = True
            event = True
            is_exit = True
            shares = state["shares"]
            cost_basis = state["cost_basis"]
            gross_proceeds = shares * exit_price
            commission = gross_proceeds * commission_pct
            net_proceeds = gross_proceeds - commission
            pnl = net_proceeds - cost_basis
            return_pct = pnl / cost_basis if cost_basis else 0.0

            state["cash"] += net_proceeds
            trade = {
                "entry_date": state["entry_date"],
                "exit_date": as_of,
                "entry_price": state["entry_price"],
                "exit_price": exit_price,
                "shares": shares,
                "pnl": pnl,
                "return_pct": return_pct,
                "exit_reason": exit_reason,
            }
            state["trade_log"].append(trade)
            record_trade(symbol, market, strategy_name, trade)
            state.update(
                in_position=False,
                entry_date=None,
                entry_price=None,
                shares=0.0,
                cost_basis=0.0,
                stop_level=None,
                target_level=None,
            )

            label = {"stop": "โดน STOP-LOSS", "target": "ถึงเป้า TAKE-PROFIT", "signal": "สัญญาณกลยุทธ์บอกให้ออก"}[exit_reason]
            lines.append(f">>> {label} ที่ {exit_price:.5f} — ปิดสถานะ")
            lines.append(f"    กำไร/ขาดทุน: {pnl:+,.2f} ({return_pct*100:+.2f}%)")
            lines.append(f"    เงินสดคงเหลือ: {state['cash']:,.2f}")
            # Originally treated as "informational only" — wrong. Anyone actually holding a
            # real position alongside the paper signal needs to know to sell just as urgently
            # as they needed to know to buy (2026-08-21: Boss reported a real TAKE-PROFIT exit
            # this same shape, missed because it wasn't mentioned/individually delivered).
            quick_link = _quick_action_link(symbol, market)
            if quick_link:
                lines.append(f"    🔗 เปิดหน้าเทรด: {quick_link}")
            lines.append("    ⚡ ถ้าขายไม้นี้จริงแล้ว ตอบ ✅ ใต้ข้อความนี้ — ถ้ายังไม่ได้ขาย ตอบ ❌")
            lines.append(f"[trade-exit:{symbol}:{market}:price={exit_price:.5f}:reason={exit_reason}:pnl={pnl:+.2f}]")
        else:
            unrealized = state["shares"] * latest_close - state["cost_basis"]
            lines.append(f"สถานะ: ถือ LONG อยู่ (เข้าเมื่อ {state['entry_date']} ที่ {state['entry_price']:.5f})")
            lines.append(f"กำไร/ขาดทุนที่ยังไม่รับรู้: {unrealized:+,.2f}")
            if stop_level:
                lines.append(f"Stop-loss: {stop_level:.5f}  (ห่างจากราคาปัจจุบัน {(latest_close/stop_level-1)*100:+.2f}%)")
            if target_level:
                lines.append(f"Take-profit: {target_level:.5f}  (ห่างจากราคาปัจจุบัน {(latest_close/target_level-1)*100:+.2f}%)")
            lines.append(">>> คำแนะนำ: ถือต่อ (HOLD)")

    if not state["in_position"] and just_exited:
        # Mirrors the backtest engine's forced_exit rule: no re-entry on the same bar a
        # position closed. Wait for the next check-in to consider a fresh entry.
        lines.append(">>> เพิ่งปิดสถานะไปเมื่อครู่ — รอเช็กรอบถัดไปก่อนพิจารณาเข้าใหม่ (กันเข้า-ออกวันเดียวกัน)")
    elif not state["in_position"]:
        if signal_now == 1 and not allow_entry:
            lines.append(
                ">>> สัญญาณ BULLISH แต่ถูกบล็อกโดย correlation guard "
                "(ครบโควตาจำนวนสถานะเปิดพร้อมกันในตลาดนี้แล้ว) — ข้ามไม้นี้"
            )
        elif signal_now == 1:
            fill_price = latest_close * (1 + slippage_pct)
            allocate = compute_entry_allocation(
                state["cash"], fill_price, commission_pct, sizing_mode, size_pct, risk_pct, stop_pct, state["trade_log"]
            )
            if allocate > 0:
                event = True
                is_entry = True
                shares = allocate / fill_price
                gross_cost = shares * fill_price
                commission = gross_cost * commission_pct
                cost_basis = gross_cost + commission
                stop_level = fill_price * (1 - stop_pct) if stop_pct else None
                target_level = fill_price * (1 + target_pct) if target_pct else None

                state["cash"] -= cost_basis
                state.update(
                    in_position=True,
                    entry_date=as_of,
                    entry_price=fill_price,
                    shares=shares,
                    cost_basis=cost_basis,
                    stop_level=stop_level,
                    target_level=target_level,
                )
                record_entry(symbol, market, strategy_name, as_of, fill_price)
                lines.append(f">>> คำแนะนำ: เข้า LONG ที่ ~{fill_price:.5f}, ขนาด {shares:,.4f} หน่วย (ใช้เงิน {cost_basis:,.2f})")
                if stop_level:
                    lines.append(f"    ตั้ง stop-loss ที่ {stop_level:.5f}")
                if target_level:
                    lines.append(f"    ตั้ง take-profit ที่ {target_level:.5f}")
                staleness_warning = _live_price_deviation_warning(symbol, market, fill_price)
                if staleness_warning:
                    lines.append(staleness_warning)
                quick_link = _quick_action_link(symbol, market)
                if quick_link:
                    lines.append(f"    🔗 เปิดหน้าเทรด: {quick_link}")
                lines.append("    ⚡ ถ้าเข้าไม้นี้จริง ตอบ ✅ ใต้ข้อความนี้ — ถ้าข้าม ตอบ ❌ (ไม่ต้องพิมพ์อะไรเพิ่ม)")
                stop_str = f"{stop_level:.5f}" if stop_level else "none"
                target_str = f"{target_level:.5f}" if target_level else "none"
                lines.append(
                    f"[trade-signal:{symbol}:{market}:entry={fill_price:.5f}:stop={stop_str}:target={target_str}:size={shares:.6f}]"
                )
            else:
                lines.append(">>> สัญญาณอยากเข้า LONG แต่คำนวณขนาดออเดอร์ได้ 0 (เช็ค --stop-pct/--risk-pct)")
        else:
            lines.append("สถานะ: ไม่มีสถานะ (เงินสด)")
            lines.append(">>> คำแนะนำ: ยังไม่เข้า รอสัญญาณ (WAIT)")

    save_state(path, state)
    lines.append("-" * 60)
    lines.append(f"เงินทุนเริ่มต้น {state['initial_capital']:,.2f} | เงินสด+มูลค่าถือครองตอนนี้ {state['cash'] + state['shares']*latest_close:,.2f}")
    lines.append(f"[state file: {path}]")
    return AdviseResult(report="\n".join(lines), event=event, is_entry=is_entry, is_exit=is_exit)
