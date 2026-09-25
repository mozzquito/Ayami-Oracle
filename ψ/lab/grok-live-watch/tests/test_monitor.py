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


def _tracked(symbol: str, entry: float, last_id: int) -> MonitorState:
    return MonitorState(
        positions={
            symbol: PositionState(
                symbol=symbol,
                opened_at=datetime.now(timezone.utc).isoformat(),
                entry_price=entry,
                last_trade_id=last_id,
            )
        }
    )


def test_sell_leaving_rounding_dust_closes_the_position() -> None:
    """Live 2026-09-25: TRX sold 28.6 of 28.7, 0.093 (~$0.03) left behind. The old
    qty<=1e-8 rule never closed it, producing false '3 open positions' / 'past SL' alerts."""
    client = FakeClient(
        balances=[{"asset": "TRX", "free": "0.0931", "locked": "0"}],
        prices={"TRXUSDT": 0.3437},
        trades={"TRXUSDT": [{"id": 8, "price": "0.3437", "qty": "28.6", "isBuyer": False}]},
    )
    result = poll_once(client, _tracked("TRXUSDT", 0.3473, 7))

    assert "TRXUSDT" not in result.state.positions
    assert any("Closed TRXUSDT" in line and "pnl≈-1.04%" in line for line in result.lines)


def test_dust_leftover_with_price_failure_is_kept_not_closed() -> None:
    """Price-failure safety still holds for the new dust rule: no price, no close."""
    client = FakeClient(
        balances=[{"asset": "TRX", "free": "0.0931", "locked": "0"}],
        prices={},
        trades={},
    )
    result = poll_once(client, _tracked("TRXUSDT", 0.3473, 7))

    assert "TRXUSDT" in result.state.positions
    assert not any("Closed" in line for line in result.lines)


def test_real_position_above_min_usd_stays_tracked() -> None:
    client = FakeClient(
        balances=[{"asset": "ETH", "free": "0.00378", "locked": "0"}],
        prices={"ETHUSDT": 2690.0},
        trades={},
    )
    result = poll_once(client, _tracked("ETHUSDT", 2691.59, 5))

    assert "ETHUSDT" in result.state.positions
    assert not any("Closed" in line for line in result.lines)


def test_exit_and_reentry_between_polls_resets_entry_price() -> None:
    """Live 2026-09-25: ETH exited 09-23 (dust left) and re-bought 09-25 @2691.59; the
    monitor kept the old 2750.36 entry and raised a false '-2.53% past SL' alert."""
    buy_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    client = FakeClient(
        balances=[{"asset": "ETH", "free": "0.003781", "locked": "0"}],
        prices={"ETHUSDT": 2683.0},
        trades={
            "ETHUSDT": [
                {"id": 6, "price": "2719.98", "qty": "0.0036", "isBuyer": False},
                {"id": 7, "price": "2691.59", "qty": "0.0037", "isBuyer": True, "time": buy_ms},
            ]
        },
    )
    result = poll_once(client, _tracked("ETHUSDT", 2750.36, 5))

    pos = result.state.positions["ETHUSDT"]
    assert pos.entry_price == 2691.59
    assert pos.last_trade_id == 7
    assert any("Re-opened ETHUSDT" in line for line in result.lines)
    assert not any("past the snapshot" in line for line in result.lines)


def test_close_after_missed_round_trips_does_not_invent_pnl() -> None:
    client = FakeClient(
        balances=[{"asset": "DOGE", "free": "0.289", "locked": "0"}],
        prices={"DOGEUSDT": 0.0945},
        trades={
            "DOGEUSDT": [
                {"id": 6, "price": "0.1017", "qty": "100", "isBuyer": False},
                {"id": 7, "price": "0.0957", "qty": "104", "isBuyer": True},
                {"id": 8, "price": "0.0945", "qty": "104", "isBuyer": False},
            ]
        },
    )
    result = poll_once(client, _tracked("DOGEUSDT", 0.09986, 5))

    closed = next(line for line in result.lines if "Closed DOGEUSDT" in line)
    assert "pnl" not in closed


def test_reentry_detected_when_exit_was_consumed_by_an_earlier_poll() -> None:
    """Exit sell seen in poll N (kept: price lookup failed), re-buy lands in poll N+1 —
    the new fills alone contain no sell, but the pre-buy holding was dust."""
    client = FakeClient(
        balances=[{"asset": "ETH", "free": "0.003781", "locked": "0"}],
        prices={"ETHUSDT": 2683.0},
        trades={
            "ETHUSDT": [
                {"id": 6, "price": "2719.98", "qty": "0.0036", "isBuyer": False},
                {"id": 7, "price": "2691.59", "qty": "0.0037", "isBuyer": True},
            ]
        },
    )
    result = poll_once(client, _tracked("ETHUSDT", 2750.36, 6))  # sell 6 already seen

    assert result.state.positions["ETHUSDT"].entry_price == 2691.59


def test_partial_sell_then_scale_in_keeps_cost_basis() -> None:
    client = FakeClient(
        balances=[{"asset": "ETH", "free": "0.0060", "locked": "0"}],
        prices={"ETHUSDT": 2700.0},
        trades={
            "ETHUSDT": [
                {"id": 6, "price": "2720.0", "qty": "0.0010", "isBuyer": False},
                {"id": 7, "price": "2690.0", "qty": "0.0020", "isBuyer": True},
            ]
        },
    )
    result = poll_once(client, _tracked("ETHUSDT", 2750.0, 5))

    assert result.state.positions["ETHUSDT"].entry_price == 2750.0
    assert not any("Re-opened" in line for line in result.lines)


def test_split_entry_fills_do_not_suppress_exit_pnl() -> None:
    client = FakeClient(
        balances=[],
        prices={},
        trades={
            "DOGEUSDT": [
                {"id": 6, "price": "0.1000", "qty": "50", "isBuyer": True},  # late split fill
                {"id": 7, "price": "0.1015", "qty": "100", "isBuyer": False},
            ]
        },
    )
    result = poll_once(client, _tracked("DOGEUSDT", 0.1000, 5))

    closed = next(line for line in result.lines if "Closed DOGEUSDT" in line)
    assert "pnl≈+1.50%" in closed
