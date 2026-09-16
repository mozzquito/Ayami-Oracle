"""Portfolio MAX_OPEN cap and blocked_by_cap logging."""

from __future__ import annotations

from paper_trading.portfolio import Portfolio


def test_max_open_blocks_excess_entries():
    pf = Portfolio(slot_usd=10.0, max_open=5)
    symbols = [f"S{i}USDT" for i in range(8)]
    records = []
    for i, sym in enumerate(symbols):
        rec = pf.try_enter(
            symbol=sym,
            strategy="book_rsi_ma_mtf",
            price=100.0 + i,
            bar_date="2026-09-15",
            ts_utc="2026-09-16T00:00:00Z",
            reason="rsi_cross_up_trend",
        )
        records.append(rec)

    opened = [r for r in records if r.qty > 0 and r.reason != "blocked_by_cap"]
    blocked = [r for r in records if r.reason == "blocked_by_cap"]
    assert len(opened) == 5
    assert len(blocked) == 3
    assert pf.open_count() == 5
    assert all(b.qty == 0.0 for b in blocked)
    assert all(b.side == "buy" for b in blocked)


def test_deterministic_pair_keys_independent():
    pf = Portfolio(slot_usd=10.0, max_open=5)
    r1 = pf.try_enter(
        symbol="BTCUSDT",
        strategy="book_rsi_ma_mtf",
        price=50000.0,
        bar_date="2026-09-15",
        ts_utc="2026-09-16T00:00:00Z",
        reason="rsi_cross_up_trend",
    )
    r2 = pf.try_enter(
        symbol="BTCUSDT",
        strategy="rsrs_trend",
        price=50000.0,
        bar_date="2026-09-15",
        ts_utc="2026-09-16T00:00:00Z",
        reason="rsrs_cross_up",
    )
    assert r1.qty > 0 and r2.qty > 0
    assert pf.open_count() == 2


def test_exit_frees_slot_for_new_entry():
    pf = Portfolio(slot_usd=10.0, max_open=1)
    pf.try_enter(
        symbol="ETHUSDT",
        strategy="rsrs_trend",
        price=2000.0,
        bar_date="2026-09-14",
        ts_utc="2026-09-15T00:00:00Z",
        reason="rsrs_cross_up",
    )
    blocked = pf.try_enter(
        symbol="BTCUSDT",
        strategy="rsrs_trend",
        price=50000.0,
        bar_date="2026-09-15",
        ts_utc="2026-09-16T00:00:00Z",
        reason="rsrs_cross_up",
    )
    assert blocked.reason == "blocked_by_cap"
    sold = pf.exit(
        symbol="ETHUSDT",
        strategy="rsrs_trend",
        price=2100.0,
        bar_date="2026-09-15",
        ts_utc="2026-09-16T00:00:00Z",
        reason="take_profit",
    )
    assert sold is not None and sold.pnl_usd > 0
    ok = pf.try_enter(
        symbol="BTCUSDT",
        strategy="rsrs_trend",
        price=50000.0,
        bar_date="2026-09-15",
        ts_utc="2026-09-16T00:00:00Z",
        reason="rsrs_cross_up",
    )
    assert ok.qty > 0
    assert pf.open_count() == 1
