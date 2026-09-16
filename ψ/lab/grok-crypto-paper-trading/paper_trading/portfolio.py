"""Paper portfolio: $SLOT_USD slots, MAX_OPEN cap, blocked_by_cap logging."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Position:
    symbol: str
    strategy: str
    qty: float
    entry_price: float
    entry_bar_date: str
    notional_usd: float

    def key(self) -> str:
        return f"{self.symbol}|{self.strategy}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "strategy": self.strategy,
            "qty": self.qty,
            "entry_price": self.entry_price,
            "entry_bar_date": self.entry_bar_date,
            "notional_usd": self.notional_usd,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Position":
        return cls(
            symbol=d["symbol"],
            strategy=d["strategy"],
            qty=float(d["qty"]),
            entry_price=float(d["entry_price"]),
            entry_bar_date=d["entry_bar_date"],
            notional_usd=float(d["notional_usd"]),
        )


@dataclass
class TradeRecord:
    ts_utc: str
    bar_date: str
    symbol: str
    strategy: str
    side: str
    reason: str
    price: float
    qty: float
    pnl_usd: float
    note: str = ""

    def to_row(self) -> dict[str, Any]:
        return {
            "ts_utc": self.ts_utc,
            "bar_date": self.bar_date,
            "symbol": self.symbol,
            "strategy": self.strategy,
            "side": self.side,
            "reason": self.reason,
            "price": self.price,
            "qty": self.qty,
            "pnl_usd": self.pnl_usd,
            "note": self.note,
        }


@dataclass
class Portfolio:
    slot_usd: float = 10.0
    max_open: int = 5
    cash_usd: float = 0.0  # tracking residual; starts 0, entries spend slot from virtual book
    positions: dict[str, Position] = field(default_factory=dict)
    realized_pnl_usd: float = 0.0

    def open_count(self) -> int:
        return len(self.positions)

    def get(self, symbol: str, strategy: str) -> Position | None:
        return self.positions.get(f"{symbol}|{strategy}")

    def mark_equity(self, mark_prices: dict[str, float]) -> float:
        """cash + sum(qty * mark) + treat spent slots as already deducted from cash model.

        Accounting model:
        - Start cash = 0; each entry: cash -= slot_usd, hold qty = slot/price
        - Equity = cash + sum(qty * mark_price) + realized already in cash via exits
        Actually simpler: we track cash that starts at 0. On entry cash decreases by
        slot_usd (can go negative as 'deployed capital'). On exit cash += qty*exit_price,
        and we remove position. Equity = cash + open MTMs.
        Initial empty equity = 0. After first $10 buy: cash=-10, position worth ~10, equity~0.
        """
        mtm = 0.0
        for pos in self.positions.values():
            px = mark_prices.get(pos.symbol, pos.entry_price)
            mtm += pos.qty * px
        return self.cash_usd + mtm

    def try_enter(
        self,
        *,
        symbol: str,
        strategy: str,
        price: float,
        bar_date: str,
        ts_utc: str,
        reason: str,
    ) -> TradeRecord:
        key = f"{symbol}|{strategy}"
        if key in self.positions:
            return TradeRecord(
                ts_utc=ts_utc,
                bar_date=bar_date,
                symbol=symbol,
                strategy=strategy,
                side="buy",
                reason="already_open",
                price=price,
                qty=0.0,
                pnl_usd=0.0,
                note="ignored",
            )
        if self.open_count() >= self.max_open:
            return TradeRecord(
                ts_utc=ts_utc,
                bar_date=bar_date,
                symbol=symbol,
                strategy=strategy,
                side="buy",
                reason="blocked_by_cap",
                price=price,
                qty=0.0,
                pnl_usd=0.0,
                note=f"max_open={self.max_open}",
            )
        if price <= 0:
            return TradeRecord(
                ts_utc=ts_utc,
                bar_date=bar_date,
                symbol=symbol,
                strategy=strategy,
                side="buy",
                reason="invalid_price",
                price=price,
                qty=0.0,
                pnl_usd=0.0,
                note="",
            )
        qty = self.slot_usd / price
        self.cash_usd -= self.slot_usd
        self.positions[key] = Position(
            symbol=symbol,
            strategy=strategy,
            qty=qty,
            entry_price=price,
            entry_bar_date=bar_date,
            notional_usd=self.slot_usd,
        )
        return TradeRecord(
            ts_utc=ts_utc,
            bar_date=bar_date,
            symbol=symbol,
            strategy=strategy,
            side="buy",
            reason=reason,
            price=price,
            qty=qty,
            pnl_usd=0.0,
            note="opened",
        )

    def exit(
        self,
        *,
        symbol: str,
        strategy: str,
        price: float,
        bar_date: str,
        ts_utc: str,
        reason: str,
    ) -> TradeRecord | None:
        key = f"{symbol}|{strategy}"
        pos = self.positions.get(key)
        if pos is None:
            return None
        proceeds = pos.qty * price
        pnl = proceeds - pos.notional_usd
        self.cash_usd += proceeds
        self.realized_pnl_usd += pnl
        del self.positions[key]
        return TradeRecord(
            ts_utc=ts_utc,
            bar_date=bar_date,
            symbol=symbol,
            strategy=strategy,
            side="sell",
            reason=reason,
            price=price,
            qty=pos.qty,
            pnl_usd=pnl,
            note="closed",
        )

    def to_state(self) -> dict[str, Any]:
        return {
            "cash_usd": self.cash_usd,
            "realized_pnl_usd": self.realized_pnl_usd,
            "positions": [p.to_dict() for p in self.positions.values()],
        }

    @classmethod
    def from_state(
        cls,
        state: dict[str, Any],
        slot_usd: float,
        max_open: int,
    ) -> "Portfolio":
        pf = cls(slot_usd=slot_usd, max_open=max_open)
        pf.cash_usd = float(state.get("cash_usd", 0.0))
        pf.realized_pnl_usd = float(state.get("realized_pnl_usd", 0.0))
        for d in state.get("positions", []):
            pos = Position.from_dict(d)
            pf.positions[pos.key()] = pos
        return pf
