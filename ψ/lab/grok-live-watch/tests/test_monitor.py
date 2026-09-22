"""Tests for the poll/diff loop — no network calls, a fake client stands in for
BinanceTHClient (same shape: account(), ticker_price(), user_trades())."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from live_watch.monitor import STALE_AFTER, poll_once
from live_watch.state import MonitorState, PositionState


class FakeClient:
    def __init__(
        self,
        balances: list[dict[str, Any]],
        prices: dict[str, float],
        trades: dict[str, list[dict[str, Any]]],
    ) -> None:
        self._balances = balances
        self._prices = prices
        self._trades = trades

    def account(self) -> dict[str, Any]:
        return {"balances": self._balances}

    def ticker_price(self, symbol: str) -> float:
        if symbol not in self._prices:
            raise KeyError(symbol)  # mirrors client.py raising on an unpriced/delisted pair
        return self._prices[symbol]

    def user_trades(self, symbol: str, limit: int = 50) -> list[dict[str, Any]]:
        return self._trades.get(symbol, [])


def test_new_position_detected_as_opened() -> None:
    client = FakeClient(
        balances=[{"asset": "BTC", "free": "0.001", "locked": "0"}],
        prices={"BTCUSDT": 50000.0},
        trades={"BTCUSDT": [{"id": 1, "price": "49900.0", "qty": "0.001", "isBuyer": True}]},
    )
    result = poll_once(client, MonitorState())

    assert "BTCUSDT" in result.state.positions
    assert result.state.positions["BTCUSDT"].entry_price == 49900.0
    assert any("Opened BTCUSDT" in line for line in result.lines)


def test_dust_below_min_usd_value_ignored() -> None:
    """Real-world case (live-checked 2026-09-22): a quantity threshold can't tell dust from
    a position — 9.89e-06 BTC is 'large' by quantity but worth <$1. Value-based filtering
    against MIN_POSITION_USD is what actually distinguishes the two."""
    client = FakeClient(
        balances=[{"asset": "BTC", "free": "0.00001", "locked": "0"}],  # ~$0.85 @ 85000
        prices={"BTCUSDT": 85000.0},
        trades={},
    )
    result = poll_once(client, MonitorState())

    assert result.state.positions == {}
    assert result.report == "No changes — positions unchanged."


def test_asset_with_no_price_lookup_excluded_not_crashed() -> None:
    client = FakeClient(
        balances=[{"asset": "SHIB", "free": "1000000", "locked": "0"}],
        prices={},  # no SHIBUSDT entry -> ticker_price raises, must be swallowed
        trades={},
    )
    result = poll_once(client, MonitorState())

    assert result.state.positions == {}


def test_fiat_thb_balance_never_treated_as_a_position() -> None:
    client = FakeClient(
        balances=[{"asset": "THB", "free": "1000", "locked": "0"}],
        prices={},
        trades={},
    )
    result = poll_once(client, MonitorState())

    assert result.state.positions == {}


def test_value_above_min_usd_counted() -> None:
    client = FakeClient(
        balances=[{"asset": "TRX", "free": "28.69", "locked": "0"}],
        prices={"TRXUSDT": 0.346},  # ~$9.93, comfortably above MIN_POSITION_USD
        trades={"TRXUSDT": []},
    )
    result = poll_once(client, MonitorState())

    assert "TRXUSDT" in result.state.positions


def test_new_fill_on_held_position_reported() -> None:
    prior = MonitorState(
        positions={
            "BTCUSDT": PositionState(
                symbol="BTCUSDT",
                opened_at=datetime.now(timezone.utc).isoformat(),
                entry_price=49900.0,
                last_trade_id=1,
            )
        }
    )
    client = FakeClient(
        balances=[{"asset": "BTC", "free": "0.002", "locked": "0"}],
        prices={"BTCUSDT": 50100.0},
        trades={
            "BTCUSDT": [
                {"id": 1, "price": "49900.0", "qty": "0.001", "isBuyer": True},
                {"id": 2, "price": "50000.0", "qty": "0.001", "isBuyer": True},
            ]
        },
    )
    result = poll_once(client, prior)

    assert any("New fill BTCUSDT" in line for line in result.lines)
    assert result.state.positions["BTCUSDT"].last_trade_id == 2


def test_position_no_longer_held_reported_as_closed_with_pnl() -> None:
    prior = MonitorState(
        positions={
            "ETHUSDT": PositionState(
                symbol="ETHUSDT",
                opened_at=datetime.now(timezone.utc).isoformat(),
                entry_price=2000.0,
                last_trade_id=5,
            )
        }
    )
    client = FakeClient(
        balances=[],  # ETH no longer held
        prices={},
        trades={"ETHUSDT": [{"id": 6, "price": "2030.0", "qty": "1", "isBuyer": False}]},
    )
    result = poll_once(client, prior)

    assert "ETHUSDT" not in result.state.positions
    closed_line = next(line for line in result.lines if "Closed ETHUSDT" in line)
    assert "pnl≈+1.50%" in closed_line


def test_stale_position_flagged_once_then_throttled() -> None:
    old_open = (datetime.now(timezone.utc) - STALE_AFTER - timedelta(hours=1)).isoformat()
    prior = MonitorState(
        positions={
            "BTCUSDT": PositionState(
                symbol="BTCUSDT",
                opened_at=old_open,
                entry_price=50000.0,
                last_trade_id=1,
            )
        }
    )
    client = FakeClient(
        balances=[{"asset": "BTC", "free": "0.001", "locked": "0"}],
        prices={"BTCUSDT": 50000.0},
        trades={"BTCUSDT": [{"id": 1, "price": "50000.0", "qty": "0.001", "isBuyer": True}]},
    )
    first = poll_once(client, prior)
    assert any("Stale position BTCUSDT" in line for line in first.lines)

    # Immediately polling again with the just-updated state must not re-alert (throttled).
    second = poll_once(client, first.state)
    assert not any("Stale position" in line for line in second.lines)


def test_report_property_joins_lines_or_says_no_changes() -> None:
    client = FakeClient(balances=[], prices={}, trades={})
    result = poll_once(client, MonitorState())
    assert result.report == "No changes — positions unchanged."


# --- Regression tests for the 2026-09-22 /zcode + /agy design-review findings ---


def test_transient_price_failure_does_not_close_a_still_held_position() -> None:
    """The bug both reviewers flagged as most severe: an earlier draft used qty*price to
    decide 'still held', so a single flaky ticker_price call made a real position vanish
    from `held`, firing a false Closed (with bogus pnl) and a false re-Opened next poll.
    Closing must depend only on the raw balance qty, never on price-lookup success."""
    prior = MonitorState(
        positions={
            "BTCUSDT": PositionState(
                symbol="BTCUSDT",
                opened_at=datetime.now(timezone.utc).isoformat(),
                entry_price=50000.0,
                last_trade_id=1,
            )
        }
    )
    client = FakeClient(
        balances=[{"asset": "BTC", "free": "0.001", "locked": "0"}],  # still actually held
        prices={},  # ticker_price raises for BTCUSDT this poll (transient failure)
        trades={"BTCUSDT": [{"id": 1, "price": "50000.0", "qty": "0.001", "isBuyer": True}]},
    )
    result = poll_once(client, prior)

    assert "BTCUSDT" in result.state.positions
    assert result.state.positions["BTCUSDT"].entry_price == 50000.0  # unchanged, not rebased
    assert not any("Closed" in line for line in result.lines)
    assert not any("Opened" in line for line in result.lines)


def test_all_new_fills_reported_not_just_the_latest() -> None:
    prior = MonitorState(
        positions={
            "BTCUSDT": PositionState(
                symbol="BTCUSDT",
                opened_at=datetime.now(timezone.utc).isoformat(),
                entry_price=49900.0,
                last_trade_id=1,
            )
        }
    )
    client = FakeClient(
        balances=[{"asset": "BTC", "free": "0.003", "locked": "0"}],
        prices={"BTCUSDT": 50100.0},
        trades={
            "BTCUSDT": [
                {"id": 1, "price": "49900.0", "qty": "0.001", "isBuyer": True},
                {"id": 2, "price": "50000.0", "qty": "0.001", "isBuyer": True},
                {"id": 3, "price": "50050.0", "qty": "0.001", "isBuyer": True},
            ]
        },
    )
    result = poll_once(client, prior)

    fill_lines = [line for line in result.lines if "New fill" in line]
    assert len(fill_lines) == 2  # ids 2 and 3, not just 3
    assert result.state.positions["BTCUSDT"].last_trade_id == 3


def test_close_picks_the_sell_fill_not_the_highest_id_trade() -> None:
    """An unfiltered max(trades, key=id) could pick a stray later-id BUY (e.g. a
    re-entry fill recorded before this poll ran) as the 'exit'. Exit must come from the
    latest SELL specifically."""
    prior = MonitorState(
        positions={
            "ETHUSDT": PositionState(
                symbol="ETHUSDT",
                opened_at=datetime.now(timezone.utc).isoformat(),
                entry_price=2000.0,
                last_trade_id=5,
            )
        }
    )
    client = FakeClient(
        balances=[],  # gone -> closed
        prices={},
        trades={
            "ETHUSDT": [
                {"id": 6, "price": "2030.0", "qty": "1", "isBuyer": False},  # the real exit
                {"id": 7, "price": "1.0", "qty": "1", "isBuyer": True},  # unrelated later BUY
            ]
        },
    )
    result = poll_once(client, prior)

    closed_line = next(line for line in result.lines if "Closed ETHUSDT" in line)
    assert "exit≈2030" in closed_line
    assert "pnl≈+1.50%" in closed_line


def test_open_picks_the_buy_fill_not_a_stray_sell() -> None:
    client = FakeClient(
        balances=[{"asset": "TRX", "free": "28.69", "locked": "0"}],
        prices={"TRXUSDT": 0.346},
        trades={
            "TRXUSDT": [
                {"id": 1, "price": "9.0", "qty": "1", "isBuyer": False},  # stray old SELL
                {"id": 2, "price": "0.3473", "qty": "28.69", "isBuyer": True},  # real entry
            ]
        },
    )
    result = poll_once(client, MonitorState())

    assert result.state.positions["TRXUSDT"].entry_price == 0.3473


def test_close_with_no_matching_sell_fill_reported_without_guessing_pnl() -> None:
    prior = MonitorState(
        positions={
            "ETHUSDT": PositionState(
                symbol="ETHUSDT",
                opened_at=datetime.now(timezone.utc).isoformat(),
                entry_price=2000.0,
                last_trade_id=5,
            )
        }
    )
    client = FakeClient(balances=[], prices={}, trades={"ETHUSDT": []})
    result = poll_once(client, prior)

    closed_line = next(line for line in result.lines if "Closed ETHUSDT" in line)
    assert "pnl" not in closed_line
    assert "possibly transferred" in closed_line


def test_trade_id_as_string_from_api_does_not_crash_comparison() -> None:
    """Binance can return numeric ids as strings; comparing str > int would raise."""
    prior = MonitorState(
        positions={
            "BTCUSDT": PositionState(
                symbol="BTCUSDT",
                opened_at=datetime.now(timezone.utc).isoformat(),
                entry_price=49900.0,
                last_trade_id=1,
            )
        }
    )
    client = FakeClient(
        balances=[{"asset": "BTC", "free": "0.002", "locked": "0"}],
        prices={"BTCUSDT": 50100.0},
        trades={"BTCUSDT": [{"id": "2", "price": "50000.0", "qty": "0.001", "isBuyer": True}]},
    )
    result = poll_once(client, prior)

    assert result.state.positions["BTCUSDT"].last_trade_id == 2
