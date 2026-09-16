#!/usr/bin/env python3
"""CLI entry: one-shot paper-trading evaluation, then exit.

Safe to run more often than once a day (e.g. hourly, like the sibling market-backtester
cron) — engine.run_daily()'s own idempotency check (last_evaluated_bar_date) means an
extra run before a new daily bar has closed just logs "Idempotent skip" and exits 0; it
never re-evaluates or re-trades the same closed bar twice.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

# Allow running as `python main.py` from project root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from paper_trading.config import load_config
from paper_trading.engine import run_daily
from paper_trading.notify import send_error_alert, send_trade_alert
from paper_trading.storage import Storage


def main() -> int:
    cfg = load_config()
    storage = Storage(cfg.data_dir)
    storage.log(
        f"Starting paper run DATA_DIR={cfg.data_dir} symbols={len(cfg.symbols)} "
        f"slot={cfg.slot_usd} max_open={cfg.max_open}"
    )
    try:
        result = run_daily(cfg, storage)
    except Exception as exc:  # noqa: BLE001 — any crash here must alert, not vanish silently
        tb = traceback.format_exc()
        storage.log(f"Run crashed: {exc}")
        send_error_alert(f"Unhandled exception in run_daily():\n{tb}")
        return 1

    if not result.get("ok"):
        storage.log(f"Run failed: {result}")
        send_error_alert(f"run_daily() returned ok=False: {result}")
        return 1

    warnings = result.get("warnings") or []
    if warnings:
        storage.log(f"Run completed with {len(warnings)} symbol warning(s): {warnings}")
        send_error_alert(
            f"Run completed but {len(warnings)}/{len(cfg.symbols)} symbol(s) failed to fetch "
            f"(others processed normally):\n" + "\n".join(warnings)
        )

    if result.get("skipped"):
        return 0

    # Only real fills — a blocked_by_cap/already_open/invalid_price row has qty=0 and
    # isn't a trade that happened, so it must not alert (matches market-backtester's own
    # rule: a blocked signal is visible in the log, never a chat notification).
    for trade in result.get("trades") or []:
        is_real_fill = trade["side"] == "sell" or (trade["side"] == "buy" and trade["qty"] > 0)
        if is_real_fill:
            send_trade_alert(trade)

    storage.log(
        f"Summary bar_date={result.get('bar_date')} "
        f"trades={len(result.get('trades') or [])} "
        f"open={result.get('open_count')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
