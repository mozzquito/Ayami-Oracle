"""Paper trading strategies: book_rsi_ma_mtf and rsrs_trend."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from paper_trading.indicators import moving_average, rsi, rsrs_slope

SignalSide = Literal["enter_long", "exit_long", "hold"]


@dataclass
class Signal:
    strategy: str
    side: SignalSide
    reason: str
    price: float


def _prev_curr(series: pd.Series) -> tuple[float, float]:
    if len(series) < 2:
        raise ValueError("Need at least 2 values for crossover")
    return float(series.iloc[-2]), float(series.iloc[-1])


def evaluate_book_rsi_ma_mtf(
    bars: pd.DataFrame,
    *,
    rsi_period: int = 14,
    rsi_oversold: float = 30.0,
    trend_ma_period: int = 50,
    in_position: bool = False,
    entry_price: float | None = None,
    sl_pct: float = 0.05,
    tp_pct: float = 0.10,
) -> Signal:
    """
    RSI(14) long when RSI crosses UP through oversold (prev < 30, curr >= 30),
    gated by close > MA(trend_ma_period). Exit: 5% SL, 10% TP, or RSI back below 30.
    """
    name = "book_rsi_ma_mtf"
    closes = bars["close"]
    price = float(closes.iloc[-1])
    rsi_s = rsi(closes, rsi_period)
    ma_s = moving_average(closes, trend_ma_period)

    if len(rsi_s.dropna()) < 2 or pd.isna(ma_s.iloc[-1]):
        return Signal(name, "hold", "insufficient_data", price)

    prev_rsi, curr_rsi = _prev_curr(rsi_s)
    curr_ma = float(ma_s.iloc[-1])
    above_trend = price > curr_ma

    if in_position and entry_price is not None and entry_price > 0:
        ret = (price - entry_price) / entry_price
        if ret <= -sl_pct:
            return Signal(name, "exit_long", "stop_loss", price)
        if ret >= tp_pct:
            return Signal(name, "exit_long", "take_profit", price)
        if curr_rsi < rsi_oversold:
            return Signal(name, "exit_long", "rsi_reversal", price)
        return Signal(name, "hold", "in_position", price)

    # Entry: RSI cross up through oversold + trend gate
    crossed_up = prev_rsi < rsi_oversold and curr_rsi >= rsi_oversold
    if crossed_up and above_trend:
        return Signal(name, "enter_long", "rsi_cross_up_trend", price)
    return Signal(name, "hold", "no_entry", price)


def evaluate_rsrs_trend(
    bars: pd.DataFrame,
    *,
    rsrs_window: int = 18,
    rsrs_threshold: float = 0.0,
    in_position: bool = False,
    entry_price: float | None = None,
    sl_pct: float = 0.025,
    tp_pct: float = 0.05,
) -> Signal:
    """
    RSRS = OLS slope of close vs time over window N.
    Long when score crosses above threshold; exit 2.5% SL / 5% TP / cross below.
    """
    name = "rsrs_trend"
    closes = bars["close"]
    price = float(closes.iloc[-1])
    score = rsrs_slope(closes, rsrs_window)

    if len(score.dropna()) < 2:
        return Signal(name, "hold", "insufficient_data", price)

    prev_s, curr_s = _prev_curr(score)

    if in_position and entry_price is not None and entry_price > 0:
        ret = (price - entry_price) / entry_price
        if ret <= -sl_pct:
            return Signal(name, "exit_long", "stop_loss", price)
        if ret >= tp_pct:
            return Signal(name, "exit_long", "take_profit", price)
        if curr_s < rsrs_threshold:
            return Signal(name, "exit_long", "rsrs_reversal", price)
        return Signal(name, "hold", "in_position", price)

    crossed_up = prev_s < rsrs_threshold and curr_s >= rsrs_threshold
    if crossed_up:
        return Signal(name, "enter_long", "rsrs_cross_up", price)
    return Signal(name, "hold", "no_entry", price)
