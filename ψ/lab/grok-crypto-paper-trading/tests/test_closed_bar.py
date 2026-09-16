"""Closed-bar picker: never use today's incomplete candle."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from paper_trading.binance import select_closed_bar


def _make_klines(n: int, last_incomplete: bool, now: datetime) -> pd.DataFrame:
    """Build n daily bars ending at 'today' or yesterday depending on flag."""
    rows = []
    # Align so last open is today UTC if incomplete, else yesterday
    if last_incomplete:
        last_open_date = now.date()
    else:
        last_open_date = (now - timedelta(days=1)).date()

    for i in range(n - 1, -1, -1):
        open_date = last_open_date - timedelta(days=i)
        open_dt = datetime(
            open_date.year, open_date.month, open_date.day, 0, 0, 0, tzinfo=timezone.utc
        )
        # Binance daily close_time is typically next day 00:00 minus 1ms
        close_dt = open_dt + timedelta(days=1) - timedelta(milliseconds=1)
        rows.append(
            {
                "open_time": pd.Timestamp(open_dt),
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.0 + (n - 1 - i),
                "volume": 1.0,
                "close_time": pd.Timestamp(close_dt),
            }
        )
    return pd.DataFrame(rows)


def test_selects_index_minus_2_when_last_bar_incomplete():
    now = datetime(2026, 9, 16, 7, 0, 0, tzinfo=timezone.utc)
    df = _make_klines(5, last_incomplete=True, now=now)
    bars, closed, bar_date = select_closed_bar(df, now_utc=now)
    # Last bar is today (incomplete); closed should be yesterday = index -2
    assert bar_date == "2026-09-15"
    assert len(bars) == 4
    assert float(closed["close"]) == float(df.iloc[-2]["close"])


def test_selects_last_when_fully_closed():
    now = datetime(2026, 9, 16, 0, 5, 0, tzinfo=timezone.utc)
    # All bars fully in the past (last open = Sep 15, close_time just before now)
    df = _make_klines(5, last_incomplete=False, now=now)
    # Ensure last close_time is in the past
    assert df.iloc[-1]["close_time"].to_pydatetime() < now
    bars, closed, bar_date = select_closed_bar(df, now_utc=now)
    assert bar_date == "2026-09-15"
    assert len(bars) == 5
    assert float(closed["close"]) == float(df.iloc[-1]["close"])


def test_incomplete_by_future_close_time():
    now = datetime(2026, 9, 16, 12, 0, 0, tzinfo=timezone.utc)
    df = _make_klines(3, last_incomplete=True, now=now)
    assert df.iloc[-1]["close_time"].to_pydatetime() > now
    _, closed, bar_date = select_closed_bar(df, now_utc=now)
    assert bar_date == "2026-09-15"
    assert float(closed["close"]) == float(df.iloc[-2]["close"])


def test_needs_at_least_two_bars():
    now = datetime(2026, 9, 16, 12, 0, 0, tzinfo=timezone.utc)
    df = _make_klines(1, last_incomplete=True, now=now)
    with pytest.raises(ValueError):
        select_closed_bar(df, now_utc=now)
