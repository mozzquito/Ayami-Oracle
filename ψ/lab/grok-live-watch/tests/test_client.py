"""Tests for the read-only Binance TH client — no network calls, no real key needed."""

from __future__ import annotations

import hashlib
import hmac
from unittest.mock import MagicMock, patch
from urllib.parse import urlencode

import pytest

from live_watch.client import BinanceTHClient
from live_watch.config import Config

TEST_CONFIG = Config(
    api_key="test-api-key",
    api_secret="test-api-secret",
    base_url="https://api.binance.th",
    recv_window=5000,
)


def _fake_response(status_code: int = 200, json_body: object | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = "" if json_body is None else str(json_body)
    resp.json.return_value = json_body if json_body is not None else {}
    if status_code >= 400:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    else:
        resp.raise_for_status.return_value = None
    return resp


def test_sign_matches_independent_hmac_sha256_reference() -> None:
    """The signature must be a plain HMAC-SHA256 hex digest over the urlencoded query string
    (as documented), computed here independently of the implementation under test."""
    client = BinanceTHClient(TEST_CONFIG, session=MagicMock())
    params = {"symbol": "BTCUSDT", "timestamp": 1499827319559, "recvWindow": 5000}
    expected = hmac.new(
        TEST_CONFIG.api_secret.encode("utf-8"),
        urlencode(params).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    assert client._sign(params) == expected


def test_signed_get_sends_apikey_header_and_required_signed_params() -> None:
    session = MagicMock()
    session.get.return_value = _fake_response(200, {"ok": True})
    client = BinanceTHClient(TEST_CONFIG, session=session)

    client.account()

    assert session.headers.update.call_args[0][0] == {"X-MBX-APIKEY": "test-api-key"}
    called_url = session.get.call_args[0][0]
    called_params = session.get.call_args[1]["params"]
    assert called_url == "https://api.binance.th/api/v1/accountV2"
    assert "timestamp" in called_params
    assert called_params["recvWindow"] == 5000
    assert "signature" in called_params


def test_all_orders_and_user_trades_require_symbol_param() -> None:
    session = MagicMock()
    session.get.return_value = _fake_response(200, [])
    client = BinanceTHClient(TEST_CONFIG, session=session)

    client.all_orders("BTCUSDT")
    assert session.get.call_args[1]["params"]["symbol"] == "BTCUSDT"

    client.user_trades("ETHUSDT", limit=100)
    params = session.get.call_args[1]["params"]
    assert params["symbol"] == "ETHUSDT"
    assert params["limit"] == 100


@pytest.mark.parametrize("status_code", [429, 418])
def test_rate_limit_and_ban_responses_raise(status_code: int) -> None:
    session = MagicMock()
    session.get.return_value = _fake_response(status_code, {"msg": "blocked"})
    client = BinanceTHClient(TEST_CONFIG, session=session)

    with pytest.raises(RuntimeError):
        client.account()


def test_public_server_time_uses_no_auth_header_requirement() -> None:
    session = MagicMock()
    session.get.return_value = _fake_response(200, {"serverTime": 1234567890})
    client = BinanceTHClient(TEST_CONFIG, session=session)

    result = client.server_time()

    assert result == 1234567890
    called_params = session.get.call_args[1]["params"]
    assert "signature" not in called_params


def test_client_defines_no_write_capable_methods() -> None:
    """Hard boundary guard: this client must never grow an order-placing/cancelling method.
    Fails loudly if a future edit adds one, rather than relying on review catching it."""
    forbidden_substrings = ("place", "cancel", "create_order", "new_order", "delete", "withdraw")
    public_methods = [
        name
        for name in dir(BinanceTHClient)
        if not name.startswith("_") and callable(getattr(BinanceTHClient, name))
    ]
    for name in public_methods:
        lowered = name.lower()
        for bad in forbidden_substrings:
            assert bad not in lowered, f"BinanceTHClient.{name} looks write-capable ({bad!r})"
