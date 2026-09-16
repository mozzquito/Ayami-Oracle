"""Discord alerting for the Grok Bot paper-trading experiment — reuses the sibling
market-backtester project's bot/channel (DISCORD_BOT_TOKEN / REPORT_CHANNEL_ID env vars)
rather than provisioning new credentials. Two kinds of message:
  - error alerts (added 2026-09-16): a genuine failure — all symbols failed to fetch, an
    unhandled exception, or a partial per-symbol fetch failure — so a silent failure here
    doesn't go unnoticed for days, the same reasoning as market-backtester's heartbeat
    watchdog.
  - trade-signal alerts (added 2026-09-17, per มอส's explicit ask): every real entry/exit
    fill embeds a [grok-trade-signal:...]/[grok-trade-exit:...] marker — a distinct prefix
    from market-backtester's own [trade-signal:...]/[trade-exit:...] markers so
    discord-bot/bot.mjs's regexes (extended 2026-09-17) can tell the two experiments'
    messages apart in the same channel and log a ✅/❌ confirm the same way, into the same
    moss-real-trades.md real-money journal (tagged by source). Prices/qty are always
    fixed-decimal (.10f), never %g's scientific notation — a small-price coin like SHIB
    would otherwise print as "5.1e-06" and break the marker's own regex, the same class of
    bug already caught once in the sibling project's advisor.py.
"""

from __future__ import annotations

import os
import sys
from typing import Any

import requests

DISCORD_MAX_LEN = 2000


def _post(content: str) -> bool:
    """Best-effort — a Discord outage must never crash the run itself, so any failure to
    send is logged to stderr and swallowed, not raised."""
    token = os.environ.get("DISCORD_BOT_TOKEN")
    channel_id = os.environ.get("REPORT_CHANNEL_ID")
    if not token or not channel_id:
        print("notify: DISCORD_BOT_TOKEN/REPORT_CHANNEL_ID not set, skipping alert", file=sys.stderr)
        return False

    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
    try:
        resp = requests.post(url, headers=headers, json={"content": content}, timeout=15)
        if resp.status_code < 300:
            return True
        print(f"notify: Discord API error {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
        return False
    except requests.RequestException as e:
        print(f"notify: request failed: {e}", file=sys.stderr)
        return False


def send_error_alert(message: str) -> bool:
    budget = DISCORD_MAX_LEN - len("```\n\n```") - 40
    body = message if len(message) <= budget else message[:budget] + "\n… (truncated)"
    return _post(f"🔬 **Grok paper-trading experiment — ERROR**\n```\n{body}\n```")


def _binance_link(symbol: str) -> str:
    """symbol is a Binance pair like 'BTCUSDT' — Binance's web trade-page URL wants the
    base/quote split with an underscore ('BTC_USDT'). Every symbol in this project's
    universe quotes in USDT (see config.DEFAULT_SYMBOLS), so stripping that fixed suffix
    is safe here without needing a full base/quote parser."""
    base = symbol[:-4] if symbol.endswith("USDT") else symbol
    return f"https://www.binance.com/en/trade/{base}_USDT?type=spot"


def send_trade_alert(trade: dict[str, Any]) -> bool:
    """trade is one row from engine.run_daily()'s result['trades'] (see
    portfolio.TradeRecord.to_row()) — call only for a real fill (side == 'buy' with
    qty > 0, or side == 'sell'), not for a blocked/already_open/invalid_price no-op.

    Embeds a [grok-trade-signal:...]/[grok-trade-exit:...] marker so discord-bot/bot.mjs
    can auto-react ✅/❌ and log a confirm/skip the same way market-backtester's own
    signals do. Always fixed-decimal (.10f) — never %g — so the marker's own regex can't
    be broken by a coin whose price prints in scientific notation.
    """
    symbol = trade["symbol"]
    link = _binance_link(symbol)
    if trade["side"] == "buy":
        content = (
            f"🔬 **Grok paper-trading experiment — ENTER**\n"
            f"```\n{symbol} ({trade['strategy']}) — reason: {trade['reason']}\n"
            f"price: {trade['price']:.10f}  qty: {trade['qty']:.10f}  bar_date: {trade['bar_date']}\n"
            f"```\n🔗 {link}\n"
            f"⚡ ถ้าเข้าไม้นี้จริง ตอบ ✅ ใต้ข้อความนี้ — ถ้าข้าม ตอบ ❌\n"
            f"[grok-trade-signal:{symbol}:{trade['strategy']}:price={trade['price']:.10f}:qty={trade['qty']:.10f}]"
        )
    else:
        content = (
            f"🔬 **Grok paper-trading experiment — EXIT**\n"
            f"```\n{symbol} ({trade['strategy']}) — reason: {trade['reason']}\n"
            f"price: {trade['price']:.10f}  pnl: {trade['pnl_usd']:+.4f}  bar_date: {trade['bar_date']}\n"
            f"```\n🔗 {link}\n"
            f"⚡ ถ้าขายไม้นี้จริงแล้ว ตอบ ✅ ใต้ข้อความนี้ — ถ้ายังไม่ได้ขาย ตอบ ❌\n"
            f"[grok-trade-exit:{symbol}:{trade['strategy']}:price={trade['price']:.10f}:reason={trade['reason']}:pnl={trade['pnl_usd']:+.4f}]"
        )
    return _post(content)
