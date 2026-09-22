"""Read-only Binance TH REST client.

Hard boundary: this module defines GET-only functions against read-only account/order/trade
endpoints. It does not implement, and must never implement, any endpoint that places, cancels,
or modifies an order (POST/DELETE /api/v1/order and friends) — see the project README's "Hard
boundaries" section. If a future change to this file adds a write-capable call, that is a
violation of the project's own design and must be rejected in review.

Verified against the live docs at https://www.binance.th/api-docs/en/ on 2026-09-22 (raw HTML
grepped for exact paths/headers, not just an AI summary of the page — see
ψ/lab/grok-live-watch/README.md "Confirmed Binance TH API shape").
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any
from urllib.parse import urlencode

import requests

from .config import Config


class BinanceTHClient:
    """Thin wrapper around Binance TH's signed, read-only REST endpoints."""

    def __init__(self, config: Config, session: requests.Session | None = None) -> None:
        self._config = config
        self._session = session or requests.Session()
        self._session.headers.update({"X-MBX-APIKEY": config.api_key})

    def _sign(self, params: dict[str, Any]) -> str:
        query = urlencode(params)
        return hmac.new(
            self._config.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _signed_get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        params = dict(params or {})
        params["timestamp"] = int(time.time() * 1000)
        params.setdefault("recvWindow", self._config.recv_window)
        params["signature"] = self._sign(params)
        url = f"{self._config.base_url}{path}"
        resp = self._session.get(url, params=params, timeout=30)
        if resp.status_code == 429:
            raise RuntimeError(f"Binance TH rate limit hit (429): {resp.text[:200]}")
        if resp.status_code == 418:
            raise RuntimeError(f"Binance TH IP auto-banned (418): {resp.text[:200]}")
        resp.raise_for_status()
        return resp.json()

    def _public_get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self._config.base_url}{path}"
        resp = self._session.get(url, params=params or {}, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def server_time(self) -> int:
        """GET /api/v1/time — public, no auth. Use to check clock drift against recvWindow."""
        data = self._public_get("/api/v1/time")
        return int(data["serverTime"])

    def ticker_price(self, symbol: str) -> float:
        """GET /api/v1/ticker/price — public, no auth. Latest price for one symbol.

        Confirmed present in the raw docs HTML (grepped 2026-09-22, same session as the
        rest of this client's endpoint verification) — see README "API shape" section.
        """
        data = self._public_get("/api/v1/ticker/price", {"symbol": symbol})
        return float(data["price"])

    def account(self) -> dict[str, Any]:
        """GET /api/v1/accountV2 (SIGNED) — balances: asset/free/locked per asset."""
        return self._signed_get("/api/v1/accountV2")

    def open_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """GET /api/v1/openOrders (SIGNED). Omit symbol to fetch all open orders (weight 40)."""
        params = {"symbol": symbol} if symbol else {}
        return self._signed_get("/api/v1/openOrders", params)

    def all_orders(self, symbol: str, limit: int = 500) -> list[dict[str, Any]]:
        """GET /api/v1/allOrders (SIGNED) — order history for one symbol (symbol is required)."""
        return self._signed_get("/api/v1/allOrders", {"symbol": symbol, "limit": limit})

    def user_trades(self, symbol: str, limit: int = 500) -> list[dict[str, Any]]:
        """GET /api/v1/userTrades (SIGNED) — fill history for one symbol."""
        return self._signed_get("/api/v1/userTrades", {"symbol": symbol, "limit": limit})
