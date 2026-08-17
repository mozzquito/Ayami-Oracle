"""Rule-based strategies. Each takes the OHLCV DataFrame + params and returns a desired-position
signal Series aligned to the same index: 1 = long, 0 = flat. Long-only for v1 (no shorting).

Signals here are computed from information available AT each bar's close — the engine is
responsible for shifting the signal forward one bar before using it to size trades, so a
strategy is never executed on the same bar's close that produced it (lookahead prevention).
"""

from __future__ import annotations

import pandas as pd

from . import indicators as ind


def sma_cross(df: pd.DataFrame, fast: int = 20, slow: int = 50) -> pd.Series:
    fast_ma = ind.sma(df["Close"], fast)
    slow_ma = ind.sma(df["Close"], slow)
    return (fast_ma > slow_ma).astype(int)


def macd_cross(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
    macd_line, signal_line, _ = ind.macd(df["Close"], fast, slow, signal)
    return (macd_line > signal_line).astype(int)


def _state_machine(enter: pd.Series, exit_: pd.Series) -> pd.Series:
    """Turn boolean enter/exit conditions into a held {1,0} position series.
    Enters on `enter`, stays long until `exit_` fires, ignores enter signals while already long.
    """
    position = pd.Series(0, index=enter.index)
    holding = False
    for i, (do_enter, do_exit) in enumerate(zip(enter, exit_)):
        if holding and do_exit:
            holding = False
        elif not holding and do_enter:
            holding = True
        position.iloc[i] = int(holding)
    return position


def rsi_threshold(df: pd.DataFrame, window: int = 14, oversold: float = 30, overbought: float = 70) -> pd.Series:
    r = ind.rsi(df["Close"], window)
    enter = r < oversold
    exit_ = r > overbought
    return _state_machine(enter.fillna(False), exit_.fillna(False))


def bollinger_bounce(df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.Series:
    _, mid, lower = ind.bollinger_bands(df["Close"], window, num_std)
    enter = df["Close"] < lower
    exit_ = df["Close"] > mid
    return _state_machine(enter.fillna(False), exit_.fillna(False))


def book_rsi_ma(df: pd.DataFrame, rsi_window: int = 5, ma_window: int = 20) -> pd.Series:
    """Mirrors the feature pair used in *Deep Learning for Finance* Ch. 11's EURUSD
    example: a short-window RSI plus (Close - longer-window MA). The book feeds these
    into an LSTM regressor; here they're combined directly into a rule: long only when
    both agree on direction (RSI > 50 and price above its MA).
    """
    r = ind.rsi(df["Close"], rsi_window)
    ma = ind.sma(df["Close"], ma_window)
    bullish = (r > 50) & (df["Close"] > ma)
    return bullish.fillna(False).astype(int)


def book_rsi_ma_mtf(
    df: pd.DataFrame,
    rsi_window: int = 5,
    ma_window: int = 20,
    weekly_ma_window: int = 10,
) -> pd.Series:
    """book_rsi_ma gated by a weekly trend filter — zcode and agy both independently
    flagged multi-timeframe confirmation as the single highest-value addition when asked
    to review this system (2026-08-15): a daily RSI+MA crossover can fire against the
    grain of the larger trend, which is a classic source of whipsaw losses. Long only
    when the daily signal is bullish AND price closed the *prior completed* week above
    its weekly SMA.

    Lookahead handling: resampling to weekly with `.resample('W').last()` labels each
    bucket by its period-end date — naively reindexing that back onto daily bars would let
    a Monday "see" that same week's Friday close before the week has happened. Shifting
    the weekly series by one period *before* reindexing to daily means a daily bar only
    ever sees the trend as of the most recently *completed* week, never the one it's
    currently inside of.
    """
    daily_signal = book_rsi_ma(df, rsi_window, ma_window)

    weekly_close = df["Close"].resample("W").last()
    weekly_sma = weekly_close.rolling(weekly_ma_window).mean()
    weekly_bullish = (weekly_close > weekly_sma).shift(1)
    weekly_bullish_daily = weekly_bullish.reindex(df.index, method="ffill").fillna(False)

    return (daily_signal.astype(bool) & weekly_bullish_daily).astype(int)


def rsrs_trend(
    df: pd.DataFrame,
    period: int = 18,
    buy_threshold: float = 0.8,
    close_threshold: float = 0.5,
) -> pd.Series:
    """RSRS (Resistance-Support Relative Strength): the OLS regression slope of High on Low
    over a trailing window. A steeper slope means the recent high has been rising faster than
    the recent low — support strengthening relative to resistance, a bullish trend-strength
    signal. Enter when the slope exceeds `buy_threshold`, hold until it decays below
    `close_threshold` (asymmetric thresholds — a state machine, like `rsi_threshold` above).

    Clean-room reimplementation of the algorithm in whchien/ai-trader (GPL-3.0) — the slope
    formula (not the code) is re-derived here via the closed-form OLS slope over rolling sums
    instead of a per-bar statsmodels regression, since both compute the identical value:
    beta = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²), x=Low, y=High. Their strategy code applies the
    threshold to the *raw* slope (not the z-score-normalized variant their indicators.py also
    defines), so this mirrors that — 0.8/0.5 are raw-slope thresholds, not z-scores.
    """
    high, low = df["High"], df["Low"]
    n = period
    sum_x = low.rolling(n).sum()
    sum_y = high.rolling(n).sum()
    sum_xy = (low * high).rolling(n).sum()
    sum_x2 = (low**2).rolling(n).sum()
    denom = n * sum_x2 - sum_x**2
    beta = (n * sum_xy - sum_x * sum_y) / denom.replace(0, pd.NA)

    enter = beta > buy_threshold
    exit_ = beta < close_threshold
    return _state_machine(enter.fillna(False), exit_.fillna(False))


def adaptive_rsi(
    df: pd.DataFrame,
    rsi_length: int = 14,
    atr_length: int = 14,
    min_period: int = 8,
    max_period: int = 28,
    adaptive_sensitivity: float = 1.0,
    smoothing_length: int = 3,
    ob_level: float = 70,
    os_level: float = 30,
    extreme_ob_level: float = 80,
    extreme_os_level: float = 20,
) -> pd.Series:
    """RSI whose smoothing period shrinks in high-volatility/fast-moving markets (more
    responsive) and lengthens in calm/slow ones (more stable), instead of a fixed window.
    Enter on a plain oversold→above crossover or an extreme-oversold reversal (RSI turning up
    two bars running while still below `extreme_os_level`); exit on the mirrored overbought
    conditions. Holds while in position (state machine).

    Clean-room reimplementation of whchien/ai-trader's AdaptiveRSI (GPL-3.0) — algorithm only,
    not the code. Requires a per-bar loop (unlike this project's other indicators) because the
    EMA smoothing factor itself changes every bar based on that bar's volatility/cycle
    readings, which isn't expressible as a fixed-window pandas rolling op.
    """
    close = df["Close"]
    atr_series = ind.atr(df, atr_length)
    volatility_ratio = (atr_series / ind.sma(atr_series, atr_length)).fillna(1.0)

    price_diff_abs = close.diff().abs()
    cycle_price_change = (close - close.shift(rsi_length)).abs()
    avg_price_change = price_diff_abs.rolling(rsi_length).mean()
    cycle_factor = (cycle_price_change / (avg_price_change * rsi_length)).fillna(0.0)

    market_factor = (volatility_ratio + cycle_factor) / 2.0
    period_range = max_period - min_period
    adaptive_period = (
        max_period - market_factor * period_range * adaptive_sensitivity / 10.0
    ).clip(lower=min_period, upper=max_period)

    delta = close.diff()
    gain = delta.clip(lower=0).fillna(0.0)
    loss = (-delta.clip(upper=0)).fillna(0.0)

    n = len(close)
    rsi_raw = pd.Series(50.0, index=close.index)
    avg_gain = avg_loss = 0.0
    for i in range(n):
        period_i = adaptive_period.iloc[i]
        if pd.isna(period_i):
            rsi_raw.iloc[i] = 50.0
            continue
        alpha = 2.0 / (period_i + 1.0)
        avg_gain = alpha * gain.iloc[i] + (1.0 - alpha) * avg_gain
        avg_loss = alpha * loss.iloc[i] + (1.0 - alpha) * avg_loss
        rsi_raw.iloc[i] = 100.0 if avg_loss == 0 else 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)

    rsi_smoothed = (
        rsi_raw.ewm(alpha=2.0 / (smoothing_length + 1.0), adjust=False).mean()
        if smoothing_length > 1
        else rsi_raw
    )

    prev, prev2 = rsi_smoothed.shift(1), rsi_smoothed.shift(2)
    enter = ((rsi_smoothed >= os_level) & (prev < os_level)) | (
        (rsi_smoothed < extreme_os_level) & (rsi_smoothed > prev) & (prev < prev2)
    )
    exit_ = ((rsi_smoothed <= ob_level) & (prev > ob_level)) | (
        (rsi_smoothed > extreme_ob_level) & (rsi_smoothed < prev) & (prev > prev2)
    )
    return _state_machine(enter.fillna(False), exit_.fillna(False))


def vcp_breakout(
    df: pd.DataFrame,
    period_short: int = 10,
    period_long: int = 60,
    period_long_discount: float = 0.7,
    highest_close_window: int = 100,
    mean_vol_window: int = 20,
    sma_long: int = 250,
    sma_short: int = 60,
    recent_price_period: int = 20,
) -> pd.Series:
    """Volatility Contraction Pattern (Mark Minervini): buy a breakout to a new N-day high that
    followed a recent squeeze in both price range and volume (a "coiling" consolidation),
    confirmed by a long-term uptrend and a currently narrow trading channel. Exit when price
    falls back below the shorter trend average.

    Clean-room reimplementation of whchien/ai-trader's VCPPattern + VCPStrategy (GPL-3.0) —
    algorithm only, not the code. Deviation: the original strategy also required
    `volume * close > 2,000,000` as a fixed-dollar liquidity filter — that's a single-market,
    single-currency threshold (tuned for US/TW-stock share volumes) that doesn't generalize
    across this project's crypto/forex watchlist with wildly different units and price scales,
    so it's dropped; the pattern's own relative volume conditions (contraction + above-average
    volume on breakout) already provide a liquidity check that *is* market-agnostic.
    """
    close, high, low, volume = df["Close"], df["High"], df["Low"], df["Volume"]

    volume_reduce = ind.sma(volume, period_short) < ind.sma(volume, period_long) * period_long_discount
    price_contract = close.rolling(period_short).std() < close.rolling(period_long).std() * period_long_discount
    contraction_recently = (volume_reduce & price_contract).rolling(5).max().fillna(0).astype(bool)

    new_high = close == close.rolling(highest_close_window).max()
    volume_confirmed = volume > ind.sma(volume, mean_vol_window) * 0.8
    vcp = contraction_recently & new_high & volume_confirmed

    uptrend = close > ind.sma(close, sma_long)
    recent_min = close.rolling(recent_price_period).min()
    recent_max = close.rolling(recent_price_period).max()
    narrow_channel = recent_min > recent_max * 0.7

    enter = vcp & uptrend & narrow_channel
    exit_ = close < ind.sma(close, sma_short)
    return _state_machine(enter.fillna(False), exit_.fillna(False))


def risk_averse(
    df: pd.DataFrame,
    volatility_period: int = 20,
    high_low_period: int = 60,
    vol_period: int = 5,
    volatility_threshold: float = 8.0,
    high_low_threshold: float = 0.3,
) -> pd.Series:
    """Multi-factor filter for calm, liquid, range-bound-but-trending conditions: low intraday
    volatility, a fresh N-day high within the last few sessions, above-average volume, and a
    tight recent trading range. Enter only when all four agree; exit once at least half of them
    (2 of 4) deteriorate, giving some slack instead of exiting on the first wobble.

    Clean-room reimplementation of whchien/ai-trader's RiskAverseStrategy (GPL-3.0) — algorithm
    only, not the code. Deviation: the original volume condition was a fixed share-count floor
    (`volume > 100,000`) tuned for stock markets — not portable across this project's
    crypto/forex watchlist where "shares" don't mean the same thing (or exist at all, for
    forex). Replaced with a relative check (`volume > its own 20-day average`), preserving the
    original intent — confirm above-normal participation — without a market-specific unit.
    """
    open_, high, low, close, volume = df["Open"], df["High"], df["Low"], df["Close"], df["Volume"]

    prev_close = close.shift(1)
    bullish = close >= open_
    bull_vol = (prev_close - open_).abs() + (open_ - low).abs() + (low - high).abs() + (high - close).abs()
    bear_vol = (prev_close - open_).abs() + (open_ - high).abs() + (high - low).abs() + (low - close).abs()
    candle_volatility = bull_vol.where(bullish, bear_vol)
    avg_volatility_pct = ind.sma(candle_volatility, volatility_period) / ind.sma(close, volatility_period) * 100

    fresh_high = close.rolling(5).max() >= close.rolling(100).max()
    above_avg_volume = ind.sma(volume, vol_period) > ind.sma(volume, volatility_period)
    narrow_range = 1 - low.rolling(high_low_period).min() / high.rolling(high_low_period).max()

    cond1 = avg_volatility_pct < volatility_threshold
    cond2 = fresh_high
    cond3 = above_avg_volume
    cond4 = narrow_range < high_low_threshold

    conditions = pd.concat([cond1, cond2, cond3, cond4], axis=1).fillna(False)
    enter = conditions.all(axis=1)
    exit_ = (~conditions).sum(axis=1) >= 2
    return _state_machine(enter, exit_)


def triple_rsi(
    df: pd.DataFrame,
    rsi_short: int = 20,
    rsi_mid: int = 60,
    rsi_long: int = 120,
    oversold: float = 55,
    overbought: float = 75,
) -> pd.Series:
    """Multi-timeframe RSI alignment: long-term RSI confirms an uptrend, mid-term RSI confirms
    it isn't overheated, and short-term RSI confirms fresh upward momentum (sustained above
    the oversold line for 3 bars, and rising >2% over the last 2 bars). Unlike the other
    threshold strategies here, entry and exit use the *same* condition — position is held only
    while all four keep agreeing, dropped the moment any one fails (no separate exit
    threshold), matching the original's "hold only while selected" portfolio-rotation logic
    adapted to a single symbol.

    Clean-room reimplementation of whchien/ai-trader's TripleRSI indicator (GPL-3.0) —
    algorithm only, not the code. Deviation: the original is a *portfolio* rotation strategy
    (monthly rebalance across many assets, ranked by volume, top-K selected) — this project
    already handles cross-symbol position limits via `MAX_CONCURRENT_POSITIONS` (the
    correlation guard), so only the per-symbol entry signal is ported, not the rotation/ranking
    machinery.
    """
    rsi_s = ind.rsi(df["Close"], rsi_short)
    rsi_m = ind.rsi(df["Close"], rsi_mid)
    rsi_l = ind.rsi(df["Close"], rsi_long)

    cond1 = rsi_l > oversold
    cond2 = rsi_m < overbought
    cond3 = rsi_s.rolling(3).min() > oversold
    cond4 = (rsi_s / rsi_s.shift(2) - 1) > 0.02

    signal = cond1 & cond2 & cond3 & cond4
    return signal.fillna(False).astype(int)


STRATEGIES = {
    "sma_cross": sma_cross,
    "macd_cross": macd_cross,
    "rsi_threshold": rsi_threshold,
    "bollinger_bounce": bollinger_bounce,
    "book_rsi_ma": book_rsi_ma,
    "book_rsi_ma_mtf": book_rsi_ma_mtf,
    "rsrs_trend": rsrs_trend,
    "adaptive_rsi": adaptive_rsi,
    "vcp_breakout": vcp_breakout,
    "risk_averse": risk_averse,
    "triple_rsi": triple_rsi,
}
