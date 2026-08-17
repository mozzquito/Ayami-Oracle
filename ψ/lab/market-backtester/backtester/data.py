"""Historical OHLCV data access via yfinance, with per-market ticker normalization."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

from .config import MARKET_SUFFIX, VALID_MARKETS


def normalize_ticker(symbol: str, market: str) -> str:
    """Turn a bare symbol into the yfinance ticker format for the given market.

    Idempotent: a symbol that already carries the market's suffix is returned unchanged,
    so users can pass either "PTT" or "PTT.BK" with --market set.
    """
    if market not in VALID_MARKETS:
        raise ValueError(f"Unknown market '{market}', expected one of {VALID_MARKETS}")

    symbol = symbol.strip().upper()
    suffix = MARKET_SUFFIX[market]
    if not suffix or symbol.endswith(suffix):
        return symbol
    return f"{symbol}{suffix}"


def fetch_ohlcv(symbol: str, market: str, start: str, end: str | None = None) -> pd.DataFrame:
    """Fetch daily OHLCV history for one ticker. Returns columns Open/High/Low/Close/Volume,
    indexed by date, with rows missing a Close dropped (e.g. non-trading-day artifacts).
    """
    ticker = normalize_ticker(symbol, market)
    df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)

    if df.empty:
        raise ValueError(f"No data returned for '{ticker}' (market={market}). Check the symbol/date range.")

    # yfinance can return MultiIndex columns for some request shapes; flatten to the plain OHLCV names.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"])
    df.index.name = "Date"
    return df
