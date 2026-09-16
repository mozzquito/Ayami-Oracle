"""Persistence: state.json, trades.csv, equity.csv, run.log under DATA_DIR."""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paper_trading.portfolio import TradeRecord

TRADE_COLUMNS = [
    "ts_utc",
    "bar_date",
    "symbol",
    "strategy",
    "side",
    "reason",
    "price",
    "qty",
    "pnl_usd",
    "note",
]

EQUITY_COLUMNS = ["date", "equity_usd", "open_count", "cash_usd"]


class Storage:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.data_dir / "state.json"
        self.trades_path = self.data_dir / "trades.csv"
        self.equity_path = self.data_dir / "equity.csv"
        self.log_path = self.data_dir / "run.log"
        self._ensure_csvs()
        self._setup_logger()

    def _ensure_csvs(self) -> None:
        if not self.trades_path.exists():
            with self.trades_path.open("w", newline="") as f:
                csv.DictWriter(f, fieldnames=TRADE_COLUMNS).writeheader()
        if not self.equity_path.exists():
            with self.equity_path.open("w", newline="") as f:
                csv.DictWriter(f, fieldnames=EQUITY_COLUMNS).writeheader()

    def _setup_logger(self) -> None:
        self.logger = logging.getLogger("paper_trading")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        fh = logging.FileHandler(self.log_path, encoding="utf-8")
        fh.setFormatter(fmt)
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        self.logger.addHandler(fh)
        self.logger.addHandler(sh)

    def load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {
                "last_evaluated_bar_date": None,
                "cash_usd": 0.0,
                "realized_pnl_usd": 0.0,
                "positions": [],
            }
        with self.state_path.open() as f:
            return json.load(f)

    def save_state(self, state: dict[str, Any]) -> None:
        tmp = self.state_path.with_suffix(".tmp")
        with tmp.open("w") as f:
            json.dump(state, f, indent=2, sort_keys=True)
        tmp.replace(self.state_path)

    def append_trades(self, trades: list[TradeRecord]) -> None:
        if not trades:
            return
        with self.trades_path.open("a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=TRADE_COLUMNS)
            for t in trades:
                w.writerow(t.to_row())

    def append_equity(
        self,
        *,
        date: str,
        equity_usd: float,
        open_count: int,
        cash_usd: float,
    ) -> None:
        with self.equity_path.open("a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=EQUITY_COLUMNS)
            w.writerow(
                {
                    "date": date,
                    "equity_usd": round(equity_usd, 6),
                    "open_count": open_count,
                    "cash_usd": round(cash_usd, 6),
                }
            )

    def log(self, msg: str) -> None:
        self.logger.info(msg)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
