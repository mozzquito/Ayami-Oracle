"""Binance public REST — daily klines fetch and closed-bar selection."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd
import requests

KLINE_COLUMNS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "trades",
    "taker_buy_base",
    "taker_buy_quote",
    "ignore",
]

# Prefer the market-data host (often reachable from geo-restricted regions),
# then the main REST API. Override with BINANCE_BASE_URL / BINANCE_FALLBACK_URLS.
DEFAULT_FALLBACK_URLS = (
    "https://data-api.binance.vision",
    "https://api.binance.com",
)


def _candidate_bases(primary: str, extra: list[str] | None = None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for u in [primary, *(extra or []), *DEFAULT_FALLBACK_URLS]:
        u = (u or "").rstrip("/")
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def fetch_daily_klines(
    symbol: str,
    base_url: str,
    limit: int = 200,
    session: requests.Session | None = None,
    fallback_urls: list[str] | None = None,
) -> pd.DataFrame:
    """Fetch 1d klines from Binance public API. No auth required."""
    sess = session or requests.Session()
    last_err: Exception | None = None
    for base in _candidate_bases(base_url, fallback_urls):
        url = f"{base}/api/v3/klines"
        params = {"symbol": symbol, "interval": "1d", "limit": limit}
        try:
            resp = sess.get(
                url,
                params=params,
                timeout=30,
                headers={"Accept": "application/json"},
            )
            if resp.status_code in (418, 429, 451):
                last_err = requests.HTTPError(
                    f"{resp.status_code} from {base}: {resp.text[:200]}",
                    response=resp,
                )
                continue
            resp.raise_for_status()
            raw: list[list[Any]] = resp.json()
            if not isinstance(raw, list) or not raw:
                last_err = ValueError(f"empty klines from {base}")
                continue
            df = pd.DataFrame(raw, columns=KLINE_COLUMNS)
            for col in ("open", "high", "low", "close", "volume"):
                df[col] = df[col].astype(float)
            df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
            df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
            return df
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            continue
    raise RuntimeError(f"Failed to fetch klines for {symbol}: {last_err}")


def select_closed_bar(
    df: pd.DataFrame,
    now_utc: datetime | None = None,
) -> tuple[pd.DataFrame, pd.Series, str]:
    """
    Return (bars_up_to_closed, closed_bar_row, bar_date_iso).

    If the latest bar is still forming (close_time in the future, or open_time
    date is today UTC), evaluate on index -2 only. Never use today's incomplete candle.
    """
    if df is None or len(df) < 2:
        raise ValueError("Need at least 2 daily klines to select a closed bar")

    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)

    today_utc = now.date()
    last = df.iloc[-1]
    open_date = (
        last["open_time"].date()
        if hasattr(last["open_time"], "date")
        else pd.Timestamp(last["open_time"]).date()
    )
    close_time = last["close_time"]
    if hasattr(close_time, "to_pydatetime"):
        close_dt = close_time.to_pydatetime()
        if close_dt.tzinfo is None:
            close_dt = close_dt.replace(tzinfo=timezone.utc)
    else:
        close_dt = pd.Timestamp(close_time).to_pydatetime()
        if close_dt.tzinfo is None:
            close_dt = close_dt.replace(tzinfo=timezone.utc)

    incomplete = (close_dt > now) or (open_date == today_utc)

    if incomplete:
        closed_idx = len(df) - 2
    else:
        closed_idx = len(df) - 1

    if closed_idx < 0:
        raise ValueError("No closed daily bar available")

    closed = df.iloc[closed_idx]
    bars = df.iloc[: closed_idx + 1].copy()
    bar_ts = closed["open_time"]
    if hasattr(bar_ts, "date"):
        bar_date = bar_ts.date().isoformat()
    else:
        bar_date = pd.Timestamp(bar_ts).date().isoformat()
    return bars, closed, bar_date
