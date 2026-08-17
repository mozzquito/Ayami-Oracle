"""Single-asset, long-only backtest engine.

Lookahead prevention: the caller's signal is computed from information available at each
bar's close. We shift it forward one bar (`signal.shift(1)`) so a bar's trading decision
was actually knowable before that bar started, then fill at that bar's Open — never at a
Close the strategy hasn't "seen" yet.

Position sizing modes (Ch. 12, "Risk Management Essentials" of Deep Learning for Finance):
  - fixed:      allocate a flat `size_pct` fraction of available cash per entry.
  - fractional: risk `risk_pct` of the account on the trade's stop distance (requires stop_pct).
  - kelly:      f = P - Q/B (win probability P, payoff ratio B), estimated from this
                backtest's own closed trades so far, falling back to a prior until
                `MIN_TRADES_FOR_KELLY` trades have closed.

Stops/targets are resting orders: once a position is open, each subsequent bar's Low/High
is checked against the stop/target level *before* that bar's strategy-driven action is
considered, so a stop can never fire on the same bar a position was opened.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import (
    DEFAULT_CAPITAL,
    DEFAULT_COMMISSION_PCT,
    DEFAULT_KELLY_PRIOR_PAYOFF,
    DEFAULT_KELLY_PRIOR_WIN_PROB,
    DEFAULT_RISK_PCT,
    DEFAULT_SIZE_PCT,
    DEFAULT_SIZING_MODE,
    DEFAULT_SLIPPAGE_PCT,
    KELLY_MIN_FRACTION,
    MIN_TRADES_FOR_KELLY,
)


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    trades: pd.DataFrame
    initial_capital: float
    final_equity: float
    market: str = "us"


def kelly_fraction(win_prob: float, payoff_ratio: float) -> float:
    """f = P - Q/B, clipped to [0, 1] — no leverage, no negative (short) sizing in long-only v1."""
    if payoff_ratio <= 0:
        return 0.0
    f = win_prob - (1 - win_prob) / payoff_ratio
    return max(0.0, min(1.0, f))


def _current_kelly_stats(trade_log: list[dict]) -> tuple[float, float]:
    """Win probability and payoff ratio (avg win / avg loss) from closed trades so far."""
    if len(trade_log) < MIN_TRADES_FOR_KELLY:
        return DEFAULT_KELLY_PRIOR_WIN_PROB, DEFAULT_KELLY_PRIOR_PAYOFF

    wins = [t["pnl"] for t in trade_log if t["pnl"] > 0]
    losses = [-t["pnl"] for t in trade_log if t["pnl"] < 0]
    win_prob = len(wins) / len(trade_log)
    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = sum(losses) / len(losses) if losses else 0.0
    payoff_ratio = avg_win / avg_loss if avg_loss > 0 else DEFAULT_KELLY_PRIOR_PAYOFF
    return win_prob, payoff_ratio


def compute_entry_allocation(
    cash: float,
    fill_price: float,
    commission_pct: float,
    sizing_mode: str,
    size_pct: float,
    risk_pct: float,
    stop_pct: float | None,
    trade_log: list[dict],
) -> float:
    """Dollar notional to allocate to a new entry (before commission). Shared by the
    backtest engine and the live `advise` command so sizing math can't drift between the
    two — a bug fixed here (like the Kelly-lockout fix) automatically applies to both.
    """
    if sizing_mode == "fixed":
        return cash * size_pct / (1 + commission_pct)

    if sizing_mode == "fractional":
        if not stop_pct:
            return 0.0
        risk_amount = cash * risk_pct
        risk_per_share = fill_price * stop_pct
        if risk_per_share <= 0:
            return 0.0
        max_affordable = cash / (1 + commission_pct)
        return min(risk_amount / risk_per_share * fill_price, max_affordable)

    # kelly
    win_prob, payoff_ratio = _current_kelly_stats(trade_log)
    f = max(kelly_fraction(win_prob, payoff_ratio), KELLY_MIN_FRACTION)
    return cash * f / (1 + commission_pct)


def run_backtest(
    df: pd.DataFrame,
    signal: pd.Series,
    initial_capital: float = DEFAULT_CAPITAL,
    commission_pct: float = DEFAULT_COMMISSION_PCT,
    slippage_pct: float = DEFAULT_SLIPPAGE_PCT,
    size_pct: float = DEFAULT_SIZE_PCT,
    sizing_mode: str = DEFAULT_SIZING_MODE,
    risk_pct: float = DEFAULT_RISK_PCT,
    stop_pct: float | None = None,
    target_pct: float | None = None,
    market: str = "us",
) -> BacktestResult:
    if sizing_mode not in ("fixed", "fractional", "kelly"):
        raise ValueError(f"Unknown sizing_mode '{sizing_mode}', expected fixed/fractional/kelly")
    if sizing_mode == "fractional" and not stop_pct:
        raise ValueError("sizing_mode='fractional' requires --stop-pct (risk is sized off the stop distance)")

    exec_signal = signal.shift(1).fillna(0).astype(int)

    cash = initial_capital
    shares = 0.0
    position = 0
    cost_basis = 0.0
    entry_date = None
    entry_price = None
    stop_level = None
    target_level = None

    equity_curve = []
    trade_log: list[dict] = []

    def _close_position(fill_price: float, date, reason: str) -> None:
        nonlocal cash, shares, position, cost_basis, entry_date, entry_price, stop_level, target_level
        gross_proceeds = shares * fill_price
        commission = gross_proceeds * commission_pct
        net_proceeds = gross_proceeds - commission
        cash += net_proceeds
        pnl = net_proceeds - cost_basis
        trade_log.append(
            {
                "entry_date": entry_date,
                "exit_date": date,
                "entry_price": entry_price,
                "exit_price": fill_price,
                "shares": shares,
                "pnl": pnl,
                "return_pct": pnl / cost_basis if cost_basis else 0.0,
                "exit_reason": reason,
            }
        )
        shares = 0.0
        position = 0
        cost_basis = 0.0
        entry_date = None
        entry_price = None
        stop_level = None
        target_level = None

    for date, row in df.iterrows():
        target = int(exec_signal.loc[date])
        open_price = float(row["Open"])
        forced_exit = False

        if position == 1 and (stop_level is not None or target_level is not None):
            low = float(row["Low"])
            high = float(row["High"])
            if stop_level is not None and low <= stop_level:
                _close_position(stop_level, date, "stop")
                forced_exit = True
            elif target_level is not None and high >= target_level:
                _close_position(target_level, date, "target")
                forced_exit = True

        if not forced_exit:
            if target == 1 and position == 0:
                fill_price = open_price * (1 + slippage_pct)
                allocate = compute_entry_allocation(
                    cash, fill_price, commission_pct, sizing_mode, size_pct, risk_pct, stop_pct, trade_log
                )

                if allocate > 0:
                    shares = allocate / fill_price
                    gross_cost = shares * fill_price
                    commission = gross_cost * commission_pct
                    cash -= gross_cost + commission
                    cost_basis = gross_cost + commission
                    position = 1
                    entry_date = date
                    entry_price = fill_price
                    stop_level = fill_price * (1 - stop_pct) if stop_pct else None
                    target_level = fill_price * (1 + target_pct) if target_pct else None

            elif target == 0 and position == 1:
                fill_price = open_price * (1 - slippage_pct)
                _close_position(fill_price, date, "signal")

        equity_curve.append(cash + shares * float(row["Close"]))

    equity_series = pd.Series(equity_curve, index=df.index, name="equity")
    trades_df = pd.DataFrame(
        trade_log,
        columns=[
            "entry_date",
            "exit_date",
            "entry_price",
            "exit_price",
            "shares",
            "pnl",
            "return_pct",
            "exit_reason",
        ],
    )

    return BacktestResult(
        equity_curve=equity_series,
        trades=trades_df,
        initial_capital=initial_capital,
        final_equity=equity_curve[-1] if equity_curve else initial_capital,
        market=market,
    )
