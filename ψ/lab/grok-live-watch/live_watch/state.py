"""Last-seen state persistence for the poll/diff loop.

Spot balances have no native "position" object — a held position is inferred from a
non-USDT asset balance appearing in account(). This module tracks that inference across
polls (as JSON on disk, since each run is a fresh one-shot process under cron/launchd —
see README "Local cron/launchd scheduling") so monitor.py can diff "what's held now" against
"what was held last poll" to detect opens/closes/stale holds without needing a live loop.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_STATE_PATH = Path(__file__).resolve().parent.parent / "state" / "state.json"


@dataclass
class PositionState:
    symbol: str
    opened_at: str  # ISO 8601 UTC — first poll this symbol's balance was seen non-dust
    entry_price: float | None  # best-effort, from most recent BUY fill at open-detection time
    last_trade_id: int  # highest userTrades id already reported for this symbol, dedupes fills
    last_alerted_stale_at: str | None = None  # throttles repeated stale-position alerts


@dataclass
class MonitorState:
    positions: dict[str, PositionState] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {"positions": {sym: asdict(p) for sym, p in self.positions.items()}}

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "MonitorState":
        positions = {
            sym: PositionState(**p) for sym, p in (data.get("positions") or {}).items()
        }
        return cls(positions=positions)


def load_state(path: Path = DEFAULT_STATE_PATH) -> MonitorState:
    if not path.exists():
        return MonitorState()
    with path.open("r", encoding="utf-8") as f:
        return MonitorState.from_json(json.load(f))


def save_state(state: MonitorState, path: Path = DEFAULT_STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(state.to_json(), f, indent=2, sort_keys=True)
    tmp.replace(path)  # atomic swap — a crash mid-write must never leave a truncated state.json
