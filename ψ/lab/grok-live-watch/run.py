#!/usr/bin/env python3
"""CLI entry: one-shot poll, then exit. Meant to be invoked by cron/launchd on a schedule
(see README "Local cron/launchd scheduling") — no in-process loop or sleep.

Only posts to Discord when poll_once() found something worth reporting (an open, a fill, a
close, a stale-position alert, or a strategy-snapshot observation) — a "no changes" poll
stays silent so the channel isn't spammed every tick.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from live_watch.client import BinanceTHClient
from live_watch.config import load_config
from live_watch.monitor import poll_once
from live_watch.notify import send_error_alert, send_report
from live_watch.state import DEFAULT_STATE_PATH, load_state, save_state


def main() -> int:
    try:
        config = load_config()
        client = BinanceTHClient(config)
        prior_state = load_state(DEFAULT_STATE_PATH)
        result = poll_once(client, prior_state)
    except Exception as exc:  # noqa: BLE001 — any crash here must alert, not vanish silently
        tb = traceback.format_exc()
        print(f"run: crashed: {exc}", file=sys.stderr)
        send_error_alert(f"Unhandled exception in poll_once():\n{tb}")
        return 1

    save_state(result.state, DEFAULT_STATE_PATH)

    if result.lines:
        # Printed before the (best-effort) Discord send so a failed post never loses the
        # event outright — under launchd this stdout is captured to logs/poll.log (see
        # launchd/com.ayami.grok-live-watch.plist), so it's recoverable even if unseen live.
        print(result.report)
        send_report(result.report)
    else:
        print("run: no changes")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
