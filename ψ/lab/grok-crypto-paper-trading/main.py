#!/usr/bin/env python3
"""CLI entry: one-shot daily paper-trading evaluation, then exit."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as `python main.py` from project root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from paper_trading.config import load_config
from paper_trading.engine import run_daily
from paper_trading.storage import Storage


def main() -> int:
    cfg = load_config()
    storage = Storage(cfg.data_dir)
    storage.log(
        f"Starting paper run DATA_DIR={cfg.data_dir} symbols={len(cfg.symbols)} "
        f"slot={cfg.slot_usd} max_open={cfg.max_open}"
    )
    result = run_daily(cfg, storage)
    if not result.get("ok"):
        storage.log(f"Run failed: {result}")
        return 1
    if result.get("skipped"):
        return 0
    storage.log(
        f"Summary bar_date={result.get('bar_date')} "
        f"trades={len(result.get('trades') or [])} "
        f"open={result.get('open_count')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
