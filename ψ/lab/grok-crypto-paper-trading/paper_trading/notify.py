"""Error-only Discord alerting — reuses the sibling market-backtester project's bot/channel
(DISCORD_BOT_TOKEN / REPORT_CHANNEL_ID env vars) so a silent failure here doesn't go
unnoticed for days, the same reasoning as that project's heartbeat watchdog. Deliberately
error-only, not a full trade-signal feed: this experiment reports success via its own
run.log/state.json, not chat — only failures need to interrupt anyone.
"""

from __future__ import annotations

import os
import sys

import requests

DISCORD_MAX_LEN = 2000


def send_error_alert(message: str) -> bool:
    """Best-effort — a Discord outage must never crash the run itself, so any failure to
    send is logged to stderr and swallowed, not raised."""
    token = os.environ.get("DISCORD_BOT_TOKEN")
    channel_id = os.environ.get("REPORT_CHANNEL_ID")
    if not token or not channel_id:
        print("notify: DISCORD_BOT_TOKEN/REPORT_CHANNEL_ID not set, skipping alert", file=sys.stderr)
        return False

    budget = DISCORD_MAX_LEN - len("```\n\n```") - 40
    body = message if len(message) <= budget else message[:budget] + "\n… (truncated)"
    payload = {"content": f"🔬 **Grok paper-trading experiment — ERROR**\n```\n{body}\n```"}

    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code < 300:
            return True
        print(f"notify: Discord API error {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
        return False
    except requests.RequestException as e:
        print(f"notify: request failed: {e}", file=sys.stderr)
        return False
