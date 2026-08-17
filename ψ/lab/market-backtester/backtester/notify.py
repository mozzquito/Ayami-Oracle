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
import time

import requests

DISCORD_MAX_LEN = 2000
_RETRY_DELAYS_SEC = (2, 5, 10)  # 3 attempts total (1 initial + 2 retries), short backoff


def send_discord_message(message: str, mention_owner: bool = False) -> bool:
    """POSTs message to REPORT_CHANNEL_ID. Retries transient failures (network error, 5xx,
    429) up to len(_RETRY_DELAYS_SEC) extra times before giving up — a signal silently
    vanishing because of one flaky request is worse than a short delay.

    mention_owner=True prepends a real Discord @mention OUTSIDE the ```code block``` —
    Discord does not parse/ping mentions written inside a code fence, so this has to be a
    separate line before it, not just text appended into the same block.
    """
    token = os.environ.get("DISCORD_BOT_TOKEN")
    channel_id = os.environ.get("REPORT_CHANNEL_ID")
    if not token or not channel_id or channel_id == "xxx":
        print("notify: DISCORD_BOT_TOKEN/REPORT_CHANNEL_ID not set, skipping", file=sys.stderr)
        return False

    budget = DISCORD_MAX_LEN - len("```\n\n```") - 20
    body = message if len(message) <= budget else message[:budget] + "\n… (truncated)"

    prefix = ""
    if mention_owner:
        owner_id = os.environ.get("DISCORD_OWNER_ID")
        if owner_id:
            prefix = f"<@{owner_id}> "
        else:
            print("notify: mention_owner=True but DISCORD_OWNER_ID not set, sending without mention", file=sys.stderr)

    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
    payload = {"content": f"{prefix}```\n{body}\n```"}

    last_error = None
    for attempt, delay in enumerate((0, *_RETRY_DELAYS_SEC)):
        if delay:
            time.sleep(delay)
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
        except requests.RequestException as e:
            last_error = str(e)
            print(f"notify: request failed (attempt {attempt + 1}): {e}", file=sys.stderr)
            continue

        if resp.status_code < 300:
            return True
        last_error = f"{resp.status_code}: {resp.text}"
        # 4xx other than 429 (rate limit) won't succeed on retry — a bad token or bad
        # channel ID is the same error every time, so don't burn the retry budget on it.
        if resp.status_code < 500 and resp.status_code != 429:
            print(f"notify: Discord API error {last_error} (not retrying, not transient)", file=sys.stderr)
            return False
        print(f"notify: Discord API error {last_error} (attempt {attempt + 1})", file=sys.stderr)

    print(f"notify: giving up after {len(_RETRY_DELAYS_SEC) + 1} attempts — last error: {last_error}", file=sys.stderr)
    return False


def main() -> int:
    message = sys.stdin.read().strip()
    if not message:
        print("notify: nothing on stdin, nothing to send", file=sys.stderr)
        return 0
    return 0 if send_discord_message(message) else 1


if __name__ == "__main__":
    raise SystemExit(main())
