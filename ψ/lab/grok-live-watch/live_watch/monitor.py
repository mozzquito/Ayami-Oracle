"""Poll Binance TH once, diff against last-seen state, produce a text report.

Spot balances have no native "position" object, so a held position is *inferred* from
account()'s balance list. A raw quantity threshold doesn't work for classifying a *new*
candidate as a position: live-checked 2026-09-22, this account's wallet carries small
non-zero balances in ~10 assets (BTC/BNB/SOL/DOGE/etc.) that are leftover fee/rounding dust
from past trades — e.g. 9.89e-06 BTC is "large" in quantity but worth $0.85. Converting to
current USDT value and filtering against MIN_POSITION_USD is what separates dust from a
real position — confirmed live: only TRX (~$9.93) and ETH (~$10.11) crossed the threshold,
exactly matching the snapshot's max concurrent ~2 / ~10 USDT sizing.

Design review (2026-09-22, /zcode + /agy in parallel, financial-impact code — see CLAUDE.md
consult rule): both independently flagged the same critical bug in an earlier draft — using
current *value* (qty × price) to decide "still held" meant a single transient price-lookup
failure got misread as the balance having gone to zero, firing a false 🔴 Closed (with a
bogus pnl) followed by a false 🟢 Opened next poll, corrupting entry_price/opened_at. Fixed
by splitting the two concerns: whether a *previously tracked* position is still held is
decided from the **raw balance qty alone** (price-independent, can't be broken by an API
hiccup); price is only used for pnl/strategy display and for classifying a *brand-new*
candidate, and a price-lookup failure on either of those just skips that piece of output
for one poll rather than mutating state. They also flagged: entry/exit price selection
must filter trades by side (isBuyer) — an unfiltered "latest trade" could pick the wrong
leg on re-entry or on close — and multiple fills between polls must all be reported, not
just the single latest.

One call per cron/launchd tick (see README "Local cron/launchd scheduling") — no
in-process loop, no sleep.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from .client import BinanceTHClient
from .state import MonitorState, PositionState
from .strategy import SNAPSHOT, LivePosition, StrategySnapshot, evaluate

QUOTE_ASSET = "USDT"  # matches the snapshot's "Scans USDT pairs"
FIAT_ASSET = "THB"  # Binance TH's funding/fiat wallet currency — not a tradable position
DUST_QTY_ABS = 1e-8  # a raw balance at/below this is "not held", regardless of price
MIN_POSITION_USD = 2.0  # well under the snapshot's ~10 USDT size; filters wallet dust
                          # when classifying a brand-new (not yet tracked) candidate
STALE_AFTER = timedelta(hours=6)  # dead-man threshold, per README's crash-while-holding risk
STALE_REALERT_AFTER = timedelta(hours=6)  # don't re-alert every single poll once flagged
TRADE_LOOKBACK = 50  # userTrades limit — enough to cover several fills between 15min polls


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def _raw_balances(account: dict[str, Any]) -> dict[str, float]:
    """asset -> qty (free+locked) for every non-quote/fiat balance with qty > dust.
    Price-independent on purpose — see module docstring on the false-close bug."""
    balances: dict[str, float] = {}
    for bal in account.get("balances", []):
        asset = bal.get("asset")
        if not asset or asset in (QUOTE_ASSET, FIAT_ASSET):
            continue
        qty = float(bal.get("free", 0)) + float(bal.get("locked", 0))
        if qty > DUST_QTY_ABS:
            balances[asset] = qty
    return balances


def _safe_price(client: BinanceTHClient, symbol: str) -> float | None:
    try:
        return client.ticker_price(symbol)
    except (requests.exceptions.RequestException, KeyError, ValueError):
        return None


def _safe_trades(client: BinanceTHClient, symbol: str) -> list[dict[str, Any]]:
    """Best-effort fill history with ids coerced to int (Binance can return either type) —
    a fetch failure returns [] rather than raising, so callers never drop a position over
    one bad trade-history call."""
    try:
        trades = client.user_trades(symbol, limit=TRADE_LOOKBACK)
    except (requests.exceptions.RequestException, KeyError, ValueError):
        return []
    for t in trades:
        t["id"] = int(t["id"])
    return trades


def _latest_by_side(trades: list[dict[str, Any]], is_buy: bool) -> dict[str, Any] | None:
    matching = [t for t in trades if bool(t.get("isBuyer")) == is_buy]
    return max(matching, key=lambda t: t["id"]) if matching else None


@dataclass
class PollResult:
    lines: list[str]
    state: MonitorState

    @property
    def report(self) -> str:
        return "\n".join(self.lines) if self.lines else "No changes — positions unchanged."


def poll_once(
    client: BinanceTHClient,
    prior: MonitorState,
    snapshot: StrategySnapshot = SNAPSHOT,
) -> PollResult:
    account = client.account()
    raw = _raw_balances(account)
    now = _now_iso()
    lines: list[str] = []
    new_positions: dict[str, PositionState] = {}
    live_positions: list[LivePosition] = []

    for symbol, prior_pos in prior.positions.items():
        asset = symbol[: -len(QUOTE_ASSET)]
        qty = raw.get(asset, 0.0)

        if qty <= DUST_QTY_ABS:
            trades = _safe_trades(client, symbol)
            exit_trade = _latest_by_side(trades, is_buy=False)
            if exit_trade:
                exit_price = float(exit_trade["price"])
                pnl_pct = None
                if prior_pos.entry_price:
                    pnl_pct = (exit_price - prior_pos.entry_price) / prior_pos.entry_price * 100.0
                pnl_str = f", pnl≈{pnl_pct:+.2f}%" if pnl_pct is not None else ""
                lines.append(f"🔴 Closed {symbol}: exit≈{exit_price:.6f}{pnl_str}")
            else:
                lines.append(
                    f"🔴 Closed {symbol}: no matching sell fill in the last "
                    f"{TRADE_LOOKBACK} trades — balance is gone but the exit isn't "
                    f"visible here (possibly transferred out rather than sold)."
                )
            continue  # dropped from new_positions — genuinely no longer held

        # Still held by raw balance — never drop the position over a price/trade-fetch
        # hiccup; just skip that piece of output for this one poll.
        trades = _safe_trades(client, symbol)
        new_fills = sorted(
            (t for t in trades if t["id"] > prior_pos.last_trade_id), key=lambda t: t["id"]
        )
        for fill in new_fills:
            side = "BUY" if fill.get("isBuyer") else "SELL"
            lines.append(f"🔵 New fill {symbol}: {side} qty={fill['qty']} @ {fill['price']}")
        last_trade_id = new_fills[-1]["id"] if new_fills else prior_pos.last_trade_id

        updated = PositionState(
            symbol=symbol,
            opened_at=prior_pos.opened_at,
            entry_price=prior_pos.entry_price,
            last_trade_id=last_trade_id,
            last_alerted_stale_at=prior_pos.last_alerted_stale_at,
        )

        age = datetime.now(timezone.utc) - _parse_iso(prior_pos.opened_at)
        if age > STALE_AFTER:
            last_alert = (
                _parse_iso(prior_pos.last_alerted_stale_at)
                if prior_pos.last_alerted_stale_at
                else None
            )
            if last_alert is None or datetime.now(timezone.utc) - last_alert > STALE_REALERT_AFTER:
                lines.append(
                    f"⚠️ Stale position {symbol}: open {age} — check Grok Bot's sandbox "
                    f"is alive (dead-man alert, see README)."
                )
                updated.last_alerted_stale_at = now

        new_positions[symbol] = updated
        current_price = _safe_price(client, symbol)
        if current_price is not None:
            live_positions.append(LivePosition(symbol, updated.entry_price, current_price))

    for asset, qty in raw.items():
        symbol = f"{asset}{QUOTE_ASSET}"
        if symbol in prior.positions:
            continue  # already handled above

        price = _safe_price(client, symbol)
        if price is None:
            continue  # can't classify a brand-new candidate without a price — try next poll
        if qty * price < MIN_POSITION_USD:
            continue  # wallet dust, not a position

        trades = _safe_trades(client, symbol)
        entry_trade = _latest_by_side(trades, is_buy=True)
        entry_price = float(entry_trade["price"]) if entry_trade else price
        last_trade_id = entry_trade["id"] if entry_trade else 0

        new_positions[symbol] = PositionState(
            symbol=symbol,
            opened_at=now,
            entry_price=entry_price,
            last_trade_id=last_trade_id,
        )
        lines.append(f"🟢 Opened {symbol}: qty={qty:.6f} @ ~{entry_price:.6f}")
        live_positions.append(LivePosition(symbol, entry_price, price))

    lines.extend(evaluate(live_positions, snapshot))

    return PollResult(lines=lines, state=MonitorState(positions=new_positions))
