"""treade's frozen strategy snapshot, as a comparison baseline for live positions.

Source: README "Strategy snapshot" section (frozen 2026-09-22 from treade's own chat
summary — untrusted-but-useful, re-export periodically since the live strategy can drift).

Hard boundary (README "Analysis output is text only"): evaluate() only ever returns
descriptive observations ("position count exceeds snapshot's max concurrent") — never an
instruction ("you should sell X"). Do not add a recommendation/action field here.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategySnapshot:
    as_of: str = "2026-09-22"
    max_concurrent_positions: int = 2
    size_usdt: float = 10.0
    take_profit_pct: float = 1.5
    stop_loss_pct: float = 1.0
    # A live position sitting beyond this many multiples of the snapshot's TP/SL band
    # without closing suggests either a strategy drift or a stuck/crashed exit — not a
    # hard fact, just what's worth flagging for a human to look at.
    band_breach_multiplier: float = 1.5


SNAPSHOT = StrategySnapshot()


@dataclass(frozen=True)
class LivePosition:
    symbol: str
    entry_price: float | None
    current_price: float | None

    @property
    def pnl_pct(self) -> float | None:
        if not self.entry_price or not self.current_price:
            return None
        return (self.current_price - self.entry_price) / self.entry_price * 100.0


def evaluate(positions: list[LivePosition], snapshot: StrategySnapshot = SNAPSHOT) -> list[str]:
    """Return plain-English, text-only observations comparing live positions against the
    frozen snapshot. Never phrased as an instruction — see module docstring."""
    notes: list[str] = []

    if len(positions) > snapshot.max_concurrent_positions:
        notes.append(
            f"{len(positions)} open positions, above the snapshot's max concurrent "
            f"~{snapshot.max_concurrent_positions} — either the live strategy has "
            f"changed or the snapshot is stale."
        )

    for pos in positions:
        pnl = pos.pnl_pct
        if pnl is None:
            continue
        tp_ceiling = snapshot.take_profit_pct * snapshot.band_breach_multiplier
        sl_floor = -snapshot.stop_loss_pct * snapshot.band_breach_multiplier
        if pnl > tp_ceiling:
            notes.append(
                f"{pos.symbol}: +{pnl:.2f}%, well past the snapshot's ~"
                f"{snapshot.take_profit_pct:.1f}% TP without having closed — worth a look."
            )
        elif pnl < sl_floor:
            notes.append(
                f"{pos.symbol}: {pnl:.2f}%, well past the snapshot's ~"
                f"-{snapshot.stop_loss_pct:.1f}% SL without having closed — worth a look."
            )

    return notes
