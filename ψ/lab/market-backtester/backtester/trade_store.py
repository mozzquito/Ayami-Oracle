"""Shared trade history via Redis — lets the dashboard (a separate Railway service)
see closed trades from the cron job's runs, since Railway volumes are single-service
and can't be mounted on both. Position *state* still lives on the cron service's own
volume (advisor.py); this only mirrors completed trades for cross-service visibility.

Gracefully no-ops if REDIS_URL isn't set, so local dev/tests without Redis still work —
callers should treat this as best-effort, not a required dependency.
"""

from __future__ import annotations

import json
import os
import time

REDIS_KEY = "market_backtester:trade_history"
ENTRIES_KEY = "market_backtester:paper_entries"
REAL_TRADES_KEY = "market_backtester:real_trade_notes"
HEARTBEAT_KEY = "market_backtester:last_run_at"
MAX_TRADES = 2000  # cap the list so it can't grow unbounded
MAX_ENTRIES = 2000
MAX_REAL_TRADE_NOTES = 2000

_client = None
_client_checked = False


def _get_client():
    global _client, _client_checked
    if _client_checked:
        return _client
    _client_checked = True

    url = os.environ.get("REDIS_URL")
    if not url:
        return None
    try:
        import redis

        _client = redis.from_url(url, decode_responses=True, socket_connect_timeout=5)
        _client.ping()
    except Exception:
        _client = None
    return _client


def is_connected() -> bool:
    """True if Redis is configured and reachable — lets callers tell 'no trades yet'
    apart from 'Redis itself isn't working', which get_all_trades() alone can't."""
    return _get_client() is not None


def record_trade(symbol: str, market: str, strategy_name: str, trade: dict) -> None:
    """Append one closed trade to the shared history. Best-effort — a Redis outage
    should never break the advisor's own logic, so failures are swallowed silently."""
    client = _get_client()
    if client is None:
        return
    entry = {"symbol": symbol, "market": market, "strategy": strategy_name, **trade}
    try:
        client.rpush(REDIS_KEY, json.dumps(entry, default=str))
        client.ltrim(REDIS_KEY, -MAX_TRADES, -1)
    except Exception:
        pass


def record_entry(symbol: str, market: str, strategy_name: str, entry_date: str, entry_price: float) -> None:
    """Append one paper-trade entry event (not a completed trade — that's record_trade).
    Foundation for a real-vs-paper execution tracker: this is the cloud-side half (when
    did the strategy actually signal an entry). The other half — Boss's own real trades
    — lives locally in moss-real-trades.md, which this Railway-hosted Redis instance has
    no network path to (private networking only, and deliberately not exposed publicly).
    Cross-referencing the two currently requires a manual/local step, not a live dashboard
    tile — see README for the open question on how to bridge this.
    """
    client = _get_client()
    if client is None:
        return
    entry = {
        "symbol": symbol,
        "market": market,
        "strategy": strategy_name,
        "entry_date": entry_date,
        "entry_price": entry_price,
        "recorded_at": time.time(),
    }
    try:
        client.rpush(ENTRIES_KEY, json.dumps(entry, default=str))
        client.ltrim(ENTRIES_KEY, -MAX_ENTRIES, -1)
    except Exception:
        pass


def get_all_entries() -> list[dict]:
    """Returns all recorded paper-trade entry events, oldest first."""
    client = _get_client()
    if client is None:
        return []
    try:
        raw = client.lrange(ENTRIES_KEY, 0, -1)
        return [json.loads(r) for r in raw]
    except Exception:
        return []


def record_real_trade_note(text: str, symbol_hint: str | None = None) -> None:
    """Mirrors one real-trade log entry from the local Discord bot (moss-real-trades.md)
    into Redis, via the dashboard's /api/log-real-trade webhook — the bridge that lets a
    cloud-hosted dashboard show something about Boss's own real trades, which otherwise
    live only in a local, gitignored file with no network path to Railway's private Redis.

    Deliberately stores the raw text, not parsed fields — same reasoning as the local
    file itself: a misparsed number is worse than an unparsed one. This is for manual
    side-by-side comparison against the Paper Entry Log, not automated reconciliation.
    """
    client = _get_client()
    if client is None:
        return
    entry = {"text": text, "symbol_hint": symbol_hint, "recorded_at": time.time()}
    try:
        client.rpush(REAL_TRADES_KEY, json.dumps(entry, default=str))
        client.ltrim(REAL_TRADES_KEY, -MAX_REAL_TRADE_NOTES, -1)
    except Exception:
        pass


def get_all_real_trade_notes() -> list[dict]:
    """Returns all real-trade notes received via the webhook, oldest first."""
    client = _get_client()
    if client is None:
        return []
    try:
        raw = client.lrange(REAL_TRADES_KEY, 0, -1)
        return [json.loads(r) for r in raw]
    except Exception:
        return []


def record_heartbeat() -> None:
    """Marks 'the cron ran and completed successfully, right now.' Call this once at the
    end of a full cloud_run.py pass — not per-symbol. This is what lets the dashboard
    detect the exact failure mode that motivated it: the schedule silently going dead
    with no error anywhere. Best-effort, same as record_trade.
    """
    client = _get_client()
    if client is None:
        return
    try:
        client.set(HEARTBEAT_KEY, str(time.time()))
    except Exception:
        pass


def get_last_heartbeat() -> float | None:
    """Unix timestamp of the last confirmed successful run, or None if never recorded
    (or Redis unreachable — same 'no data yet, not an error' convention as elsewhere)."""
    client = _get_client()
    if client is None:
        return None
    try:
        val = client.get(HEARTBEAT_KEY)
        return float(val) if val else None
    except Exception:
        return None


def get_all_trades() -> list[dict]:
    """Returns all recorded trades, oldest first. Empty list if Redis isn't configured
    or unreachable — callers should treat that as 'no data yet', not an error."""
    client = _get_client()
    if client is None:
        return []
    try:
        raw = client.lrange(REDIS_KEY, 0, -1)
        return [json.loads(r) for r in raw]
    except Exception:
        return []
