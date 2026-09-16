"""Orchestrate one daily paper-trading evaluation."""

from __future__ import annotations

from typing import Any

import requests

from paper_trading.binance import fetch_daily_klines, select_closed_bar
from paper_trading.config import STRATEGY_ORDER, Config
from paper_trading.portfolio import Portfolio, TradeRecord
from paper_trading.storage import Storage, utc_now_iso
from paper_trading.strategies import evaluate_book_rsi_ma_mtf, evaluate_rsrs_trend


def run_daily(cfg: Config, storage: Storage | None = None) -> dict[str, Any]:
    """
    One-shot daily run:
    1. Load state; if already evaluated this closed bar date → exit early.
    2. Fetch klines per symbol; pick common closed bar date.
    3. Evaluate exits then entries with deterministic fill order.
    4. Persist state, trades, equity, log.
    """
    storage = storage or Storage(cfg.data_dir)
    state = storage.load_state()
    session = requests.Session()

    # Fetch all symbols first to determine closed bar date (use BTC as reference,
    # but verify consistency across symbols).
    bars_by_symbol: dict[str, Any] = {}
    closed_by_symbol: dict[str, Any] = {}
    bar_dates: dict[str, str] = {}

    for symbol in cfg.symbols:
        try:
            df = fetch_daily_klines(
                symbol,
                cfg.binance_base_url,
                limit=cfg.klines_limit,
                session=session,
            )
            bars, closed, bar_date = select_closed_bar(df)
            bars_by_symbol[symbol] = bars
            closed_by_symbol[symbol] = closed
            bar_dates[symbol] = bar_date
        except Exception as exc:  # noqa: BLE001
            storage.log(f"WARN skip {symbol}: {exc}")

    if not bar_dates:
        storage.log("ERROR no klines fetched; aborting")
        return {"ok": False, "reason": "no_data", "trades": []}

    # Majority / first-symbol closed bar date
    bar_date = bar_dates.get(cfg.symbols[0]) or next(iter(bar_dates.values()))
    # Prefer dates that match the primary symbols
    from collections import Counter

    date_counts = Counter(bar_dates.values())
    bar_date = date_counts.most_common(1)[0][0]

    last = state.get("last_evaluated_bar_date")
    if last == bar_date:
        storage.log(
            f"Idempotent skip: last_evaluated_bar_date={last} already processed. Exit 0."
        )
        return {
            "ok": True,
            "skipped": True,
            "bar_date": bar_date,
            "trades": [],
            "open_count": len(state.get("positions", [])),
        }

    portfolio = Portfolio.from_state(state, cfg.slot_usd, cfg.max_open)
    trades: list[TradeRecord] = []
    ts = utc_now_iso()
    mark_prices: dict[str, float] = {}

    for symbol, closed in closed_by_symbol.items():
        if bar_dates.get(symbol) != bar_date:
            storage.log(
                f"WARN {symbol} closed bar_date={bar_dates.get(symbol)} != {bar_date}; skip"
            )
            continue
        mark_prices[symbol] = float(closed["close"])

    # --- Phase 1: exits (all symbols × strategies that are open) ---
    for symbol in cfg.symbols:
        if symbol not in bars_by_symbol or bar_dates.get(symbol) != bar_date:
            continue
        bars = bars_by_symbol[symbol]
        price = mark_prices[symbol]

        for strategy in STRATEGY_ORDER:
            pos = portfolio.get(symbol, strategy)
            if pos is None:
                continue
            if strategy == "book_rsi_ma_mtf":
                sig = evaluate_book_rsi_ma_mtf(
                    bars,
                    rsi_period=cfg.rsi_period,
                    rsi_oversold=cfg.rsi_oversold,
                    trend_ma_period=cfg.trend_ma_period,
                    in_position=True,
                    entry_price=pos.entry_price,
                )
            else:
                sig = evaluate_rsrs_trend(
                    bars,
                    rsrs_window=cfg.rsrs_window,
                    rsrs_threshold=cfg.rsrs_threshold,
                    in_position=True,
                    entry_price=pos.entry_price,
                )
            if sig.side == "exit_long":
                rec = portfolio.exit(
                    symbol=symbol,
                    strategy=strategy,
                    price=price,
                    bar_date=bar_date,
                    ts_utc=ts,
                    reason=sig.reason,
                )
                if rec:
                    trades.append(rec)
                    storage.log(
                        f"EXIT {symbol} {strategy} reason={sig.reason} px={price:.6g} pnl={rec.pnl_usd:.4f}"
                    )

    # --- Phase 2: collect entry signals, sort deterministically, fill with cap ---
    entry_candidates: list[tuple[int, int, str, str, str, float]] = []
    # (symbol_idx, strategy_idx, symbol, strategy, reason, price)

    for si, symbol in enumerate(cfg.symbols):
        if symbol not in bars_by_symbol or bar_dates.get(symbol) != bar_date:
            continue
        bars = bars_by_symbol[symbol]
        price = mark_prices[symbol]

        for sti, strategy in enumerate(STRATEGY_ORDER):
            if portfolio.get(symbol, strategy) is not None:
                continue
            if strategy == "book_rsi_ma_mtf":
                sig = evaluate_book_rsi_ma_mtf(
                    bars,
                    rsi_period=cfg.rsi_period,
                    rsi_oversold=cfg.rsi_oversold,
                    trend_ma_period=cfg.trend_ma_period,
                    in_position=False,
                )
            else:
                sig = evaluate_rsrs_trend(
                    bars,
                    rsrs_window=cfg.rsrs_window,
                    rsrs_threshold=cfg.rsrs_threshold,
                    in_position=False,
                )
            if sig.side == "enter_long":
                entry_candidates.append(
                    (si, sti, symbol, strategy, sig.reason, price)
                )

    entry_candidates.sort(key=lambda x: (x[0], x[1]))

    for _, _, symbol, strategy, reason, price in entry_candidates:
        rec = portfolio.try_enter(
            symbol=symbol,
            strategy=strategy,
            price=price,
            bar_date=bar_date,
            ts_utc=ts,
            reason=reason,
        )
        trades.append(rec)
        if rec.reason == "blocked_by_cap":
            storage.log(
                f"BLOCKED {symbol} {strategy} reason=blocked_by_cap max_open={cfg.max_open}"
            )
        elif rec.side == "buy" and rec.qty > 0:
            storage.log(
                f"ENTER {symbol} {strategy} reason={reason} px={price:.6g} qty={rec.qty:.8g}"
            )

    equity = portfolio.mark_equity(mark_prices)
    new_state = portfolio.to_state()
    new_state["last_evaluated_bar_date"] = bar_date
    new_state["equity_usd"] = equity
    new_state["open_count"] = portfolio.open_count()

    storage.save_state(new_state)
    storage.append_trades(trades)
    storage.append_equity(
        date=bar_date,
        equity_usd=equity,
        open_count=portfolio.open_count(),
        cash_usd=portfolio.cash_usd,
    )

    buys = sum(1 for t in trades if t.side == "buy" and t.qty > 0)
    sells = sum(1 for t in trades if t.side == "sell")
    blocked = sum(1 for t in trades if t.reason == "blocked_by_cap")
    storage.log(
        f"DONE bar_date={bar_date} equity={equity:.4f} open={portfolio.open_count()} "
        f"buys={buys} sells={sells} blocked={blocked}"
    )

    return {
        "ok": True,
        "skipped": False,
        "bar_date": bar_date,
        "equity_usd": equity,
        "open_count": portfolio.open_count(),
        "trades": [t.to_row() for t in trades],
        "buys": buys,
        "sells": sells,
        "blocked": blocked,
    }
