"""Tests for the strategy-snapshot comparison — all descriptive, never instructive."""

from __future__ import annotations

from live_watch.strategy import SNAPSHOT, LivePosition, evaluate


def test_no_positions_no_notes() -> None:
    assert evaluate([]) == []


def test_position_within_band_produces_no_note() -> None:
    positions = [LivePosition("BTCUSDT", entry_price=100.0, current_price=100.5)]
    assert evaluate(positions) == []


def test_position_beyond_take_profit_band_flagged() -> None:
    positions = [LivePosition("BTCUSDT", entry_price=100.0, current_price=103.0)]  # +3%
    notes = evaluate(positions)
    assert len(notes) == 1
    assert "BTCUSDT" in notes[0]
    assert "TP" in notes[0]


def test_position_beyond_stop_loss_band_flagged() -> None:
    positions = [LivePosition("ETHUSDT", entry_price=100.0, current_price=97.0)]  # -3%
    notes = evaluate(positions)
    assert len(notes) == 1
    assert "ETHUSDT" in notes[0]
    assert "SL" in notes[0]


def test_position_missing_prices_skipped_silently() -> None:
    positions = [LivePosition("BTCUSDT", entry_price=None, current_price=None)]
    assert evaluate(positions) == []


def test_over_max_concurrent_flagged() -> None:
    positions = [
        LivePosition("BTCUSDT", 100.0, 100.5),
        LivePosition("ETHUSDT", 100.0, 100.5),
        LivePosition("SOLUSDT", 100.0, 100.5),
    ]
    notes = evaluate(positions)
    assert any("max concurrent" in n for n in notes)


def test_notes_never_contain_instructive_verbs() -> None:
    """README boundary: analysis output is text-only/descriptive, never order-ready."""
    positions = [
        LivePosition("BTCUSDT", 100.0, 105.0),
        LivePosition("ETHUSDT", 100.0, 90.0),
        LivePosition("SOLUSDT", 100.0, 100.0),
    ]
    forbidden = ("sell", "buy", "close position", "should trade", "place order")
    for note in evaluate(positions):
        lowered = note.lower()
        for word in forbidden:
            assert word not in lowered, f"note reads as an instruction: {note!r}"


def test_snapshot_is_frozen_and_dated() -> None:
    assert SNAPSHOT.as_of == "2026-09-22"
