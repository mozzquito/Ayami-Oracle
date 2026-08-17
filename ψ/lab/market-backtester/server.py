"""ASGI entry point for the dashboard service — wraps dashboard.py's Streamlit UI with
one extra HTTP route so the local Discord bot (a different machine, no access to
Railway's private-network-only Redis) can push a copy of real-trade log entries here.

Run with: uvicorn server:app --host 0.0.0.0 --port $PORT
(NOT `streamlit run` — that only serves the UI, not this route.)

Auth: simple shared-secret bearer token (TRADE_LOG_WEBHOOK_TOKEN), not full OAuth — this
is a personal single-writer webhook, not a public API. Still checked on every request;
a wrong/missing token gets 401, not silently ignored.
"""

from __future__ import annotations

import os

import streamlit as st
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from backtester.trade_store import record_real_trade_note

WEBHOOK_TOKEN = os.environ.get("TRADE_LOG_WEBHOOK_TOKEN")


async def log_real_trade(request: Request) -> JSONResponse:
    if not WEBHOOK_TOKEN:
        return JSONResponse({"error": "TRADE_LOG_WEBHOOK_TOKEN not configured on server"}, status_code=503)

    auth = request.headers.get("authorization", "")
    if auth != f"Bearer {WEBHOOK_TOKEN}":
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)

    text = (body.get("text") or "").strip()
    if not text:
        return JSONResponse({"error": "missing 'text' field"}, status_code=400)

    symbol_hint = body.get("symbol_hint")
    record_real_trade_note(text, symbol_hint)
    return JSONResponse({"status": "ok"})


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


app = st.App(
    "dashboard.py",
    routes=[
        Route("/api/log-real-trade", log_real_trade, methods=["POST"]),
        Route("/api/health", health, methods=["GET"]),
    ],
)
