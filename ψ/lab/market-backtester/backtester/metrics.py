"""Performance metrics computed from a BacktestResult, with asset-class-aware annualization."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import ANNUALIZATION_DAYS
from .engine import BacktestResult


@dataclass
class Metrics:
    total_return_pct: float
    cagr_pct: float
    sharpe: float
    max_drawdown_pct: float
    win_rate_pct: float
    num_trades: int
    buy_hold_return_pct: float


def _max_drawdown_pct(equity: pd.Series) -> float:
    running_max = equity.cummax()
    drawdown = (equity - running_max) / running_max
    return float(drawdown.min()) * 100


def compute_metrics(result: BacktestResult, close: pd.Series) -> Metrics:
    equity = result.equity_curve
    ann_days = ANNUALIZATION_DAYS.get(result.market, 252)

    total_return_pct = (result.final_equity / result.initial_capital - 1) * 100

    num_periods = len(equity)
    years = num_periods / ann_days if ann_days else 0
    cagr_pct = (
        ((result.final_equity / result.initial_capital) ** (1 / years) - 1) * 100
        if years > 0 and result.final_equity > 0
        else float("nan")
    )

    daily_returns = equity.pct_change().dropna()
    sharpe = (
        float(daily_returns.mean() / daily_returns.std() * np.sqrt(ann_days))
        if daily_returns.std() not in (0, None) and not daily_returns.empty
        else float("nan")
    )

    max_dd_pct = _max_drawdown_pct(equity)

    trades = result.trades
    win_rate_pct = float((trades["pnl"] > 0).mean() * 100) if not trades.empty else float("nan")

    buy_hold_return_pct = float(close.iloc[-1] / close.iloc[0] - 1) * 100

    return Metrics(
        total_return_pct=total_return_pct,
        cagr_pct=cagr_pct,
        sharpe=sharpe,
        max_drawdown_pct=max_dd_pct,
        win_rate_pct=win_rate_pct,
        num_trades=len(trades),
        buy_hold_return_pct=buy_hold_return_pct,
    )
