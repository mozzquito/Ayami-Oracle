"""One-shot Discord sender via REST API — no discord.js/Node dependency needed, so the
cloud (Railway cron) deployment stays single-runtime (Python only). Reads a message from
stdin and POSTs it to REPORT_CHANNEL_ID using DISCORD_BOT_TOKEN — same bot/channel as the
local launchd deployment's notify.mjs (ψ/lab/discord-bot/notify.mjs), just a different
transport (a plain REST call instead of a full discord.js gateway login) since a cron job
only needs to fire one message and exit, not hold a WebSocket connection open.

Usage: echo "message text" | python -m backtester.notify
"""

from __future__ import annotations

import os
import sys

import requests

DISCORD_MAX_LEN = 2000


def send_discord_message(message: str) -> bool:
    token = os.environ.get("DISCORD_BOT_TOKEN")
    channel_id = os.environ.get("REPORT_CHANNEL_ID")
    if not token or not channel_id or channel_id == "xxx":
        print("notify: DISCORD_BOT_TOKEN/REPORT_CHANNEL_ID not set, skipping", file=sys.stderr)
        return False

    budget = DISCORD_MAX_LEN - len("```\n\n```") - 20
    body = message if len(message) <= budget else message[:budget] + "\n… (truncated)"

    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json={"content": f"```\n{body}\n```"}, timeout=15)

    if resp.status_code >= 300:
        print(f"notify: Discord API error {resp.status_code}: {resp.text}", file=sys.stderr)
        return False
    return True


def main() -> int:
    message = sys.stdin.read().strip()
    if not message:
        print("notify: nothing on stdin, nothing to send", file=sys.stderr)
        return 0
    return 0 if send_discord_message(message) else 1


if __name__ == "__main__":
    raise SystemExit(main())
