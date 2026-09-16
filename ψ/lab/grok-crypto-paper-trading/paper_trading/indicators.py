"""Technical indicators: RSI, MA, RSRS (OLS slope of close vs time)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def rsi(closes: pd.Series, period: int = 14) -> pd.Series:
    """Wilder-style RSI via exponential moving average of gains/losses."""
    closes = closes.astype(float)
    delta = closes.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100.0 - (100.0 / (1.0 + rs))
    # When avg_loss is 0 and avg_gain > 0, RSI = 100
    out = out.where(~((avg_loss == 0) & (avg_gain > 0)), 100.0)
    out = out.where(~((avg_loss == 0) & (avg_gain == 0)), 50.0)
    return out


def moving_average(closes: pd.Series, period: int) -> pd.Series:
    """Simple moving average of closes."""
    return closes.astype(float).rolling(window=period, min_periods=period).mean()


def rsrs_slope(closes: pd.Series, window: int = 18) -> pd.Series:
    """
    RSRS = OLS slope of close vs time index over a rolling window.

    For each end index i, fit close[i-window+1 : i+1] ~ a + b * t
    where t = 0..window-1, and emit b.
    """
    closes = closes.astype(float).to_numpy()
    n = len(closes)
    out = np.full(n, np.nan, dtype=float)
    if window < 2 or n < window:
        return pd.Series(out)

    t = np.arange(window, dtype=float)
    t_mean = t.mean()
    t_var = ((t - t_mean) ** 2).sum()
    if t_var == 0:
        return pd.Series(out)

    for i in range(window - 1, n):
        y = closes[i - window + 1 : i + 1]
        y_mean = y.mean()
        cov = ((t - t_mean) * (y - y_mean)).sum()
        out[i] = cov / t_var

    return pd.Series(out)
