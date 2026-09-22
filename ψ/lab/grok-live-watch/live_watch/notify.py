"""Discord alerting — reuses the existing bot shared by market-backtester and
grok-crypto-paper-trading (DISCORD_BOT_TOKEN / REPORT_CHANNEL_ID env vars), per README
"Reporting channel — decided 2026-09-22". No new credential provisioned.

Unlike paper_trading/notify.py's [grok-trade-signal:...] markers, this project posts plain
informational text only — README's "Analysis output is text only" boundary: this is a
monitor watching a live agent's own trades, not a signal generator, so there is nothing
here for discord-bot/bot.mjs's confirm/skip regexes to react to.
"""

from __future__ import annotations

import os
import sys

import requests

DISCORD_MAX_LEN = 2000


def _post(content: str) -> bool:
    """Best-effort — a Discord outage must never crash the poll itself."""
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


def send_report(report: str) -> bool:
    budget = DISCORD_MAX_LEN - len("🦌☁️ **Grok Live Watch**\n```\n\n```") - 10
    body = report if len(report) <= budget else report[:budget] + "\n… (truncated)"
    return _post(f"🦌☁️ **Grok Live Watch**\n```\n{body}\n```")


def send_error_alert(message: str) -> bool:
    budget = DISCORD_MAX_LEN - len("```\n\n```") - 40
    body = message if len(message) <= budget else message[:budget] + "\n… (truncated)"
    return _post(f"🦌☁️ **Grok Live Watch — ERROR**\n```\n{body}\n```")
