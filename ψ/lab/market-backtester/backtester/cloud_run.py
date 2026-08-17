"""Cloud cron entrypoint: loops multiple symbols through `advise()` in one run and posts
ONE Discord message combining only the symbols that had a real event this check (entry,
exit, or stop/target hit) — HOLD/WAIT results are still printed to the log but don't
trigger a notification, so running this more often doesn't mean more Discord noise.

Usage: python -m backtester.cloud_run
"""

from __future__ import annotations

from datetime import datetime, timezone

from .advisor import advise, is_in_position
from .config import MAX_CONCURRENT_POSITIONS
from .notify import send_discord_message
from .trade_store import record_heartbeat

# Paper trade only — no real money. Each entry is its own independent single-asset
# position (v1 has no portfolio/cross-asset logic), sharing the same $10 capital pool
# conceptually but tracked as separate state files per symbol.
SYMBOLS = [
    {
        "symbol": "BTC",
        "market": "crypto",
        "strategy_name": "book_rsi_ma_mtf",
        "params": {},
        "capital": 10,
        "sizing_mode": "fixed",
        "stop_pct": 0.05,
        "target_pct": 0.10,
    },
    {
        "symbol": "ETH",
        "market": "crypto",
        "strategy_name": "book_rsi_ma_mtf",
        "params": {},
        "capital": 10,
        "sizing_mode": "fixed",
        "stop_pct": 0.05,
        "target_pct": 0.10,
    },
    {
        "symbol": "SOL",
        "market": "crypto",
        "strategy_name": "book_rsi_ma_mtf",
        "params": {},
        "capital": 10,
        "sizing_mode": "fixed",
        "stop_pct": 0.05,
        "target_pct": 0.10,
    },
    {
        "symbol": "TRX",
        "market": "crypto",
        # Trial (2026-08-17, user's explicit pick): rsrs_trend backtested +205.2% vs
        # book_rsi_ma_mtf's +52.7% on this symbol (2023-2026, 9-symbol comparison) — the
        # single best return/drawdown ratio of the 9 (3.56). Drawdown is worse than the
        # mtf baseline (-57.6% vs -36.6%), a real tradeoff accepted for the upside. Uses
        # config.STRATEGY_STOP_TARGET_PCT's tuned crypto distance, same as CLI default.
        "strategy_name": "rsrs_trend",
        "params": {},
        "capital": 10,
        "sizing_mode": "fixed",
        "stop_pct": 0.025,
        "target_pct": 0.05,
    },
    {
        "symbol": "BNB",
        "market": "crypto",
        "strategy_name": "book_rsi_ma_mtf",
        "params": {},
        "capital": 10,
        "sizing_mode": "fixed",
        "stop_pct": 0.05,
        "target_pct": 0.10,
    },
    {
        "symbol": "NEAR",
        "market": "crypto",
        "strategy_name": "book_rsi_ma_mtf",
        "params": {},
        "capital": 10,
        "sizing_mode": "fixed",
        "stop_pct": 0.05,
        "target_pct": 0.10,
    },
    {
        "symbol": "EURUSD",
        "market": "forex",
        "strategy_name": "book_rsi_ma_mtf",
        "params": {},
        "capital": 10,
        "sizing_mode": "fixed",
        # Forex moves in much smaller % ranges than crypto — a 5% stop would rarely
        # trigger, so this uses the tighter distance already validated earlier in this
        # session's testing (--stop-pct 0.03 --target-pct 0.06 on EURUSD).
        "stop_pct": 0.03,
        "target_pct": 0.06,
    },
    {
        "symbol": "GBPUSD",
        "market": "forex",
        # Trial (2026-08-17, user's explicit pick): rsrs_trend backtested +7.0% / -8.0%
        # max-drawdown vs book_rsi_ma_mtf's -12.9% / -15.4% on this symbol (2023-2026) —
        # better on both return AND drawdown, no tradeoff, the safer of the two trial
        # picks. Uses config.STRATEGY_STOP_TARGET_PCT's tuned forex distance.
        "strategy_name": "rsrs_trend",
        "params": {},
        "capital": 10,
        "sizing_mode": "fixed",
        "stop_pct": 0.015,
        "target_pct": 0.03,
    },
    {
        "symbol": "AUDUSD",
        "market": "forex",
        "strategy_name": "book_rsi_ma_mtf",
        "params": {},
        "capital": 10,
        "sizing_mode": "fixed",
        "stop_pct": 0.03,
        "target_pct": 0.06,
    },
]


def main() -> int:
    header = f"=== {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC ==="
    print(header)

    # Correlation guard: count positions already open per market before this run starts,
    # then keep the count updated as entries/exits happen *during* this same run — a
    # market that's already at its cap shouldn't let a 3rd, 4th, 5th signal squeeze in
    # just because they all fired in the same pass.
    open_counts: dict[str, int] = {}
    for cfg in SYMBOLS:
        market = cfg["market"]
        if is_in_position(cfg["symbol"], market, cfg["strategy_name"], cfg["capital"]):
            open_counts[market] = open_counts.get(market, 0) + 1

    # ENTER events go out as their own Discord message (not batched with the rest) — each
    # one carries a ✅/❌ reaction prompt for the quick-confirm flow (see advisor.py's
    # _quick_action_link + the [trade-signal:...] marker), and a reaction only has ONE
    # message to attach to, so two entries sharing a message would be unresolvable. Exit/
    # stop/target events are informational only (no action needed) and stay batched.
    entry_reports = []
    other_event_reports = []
    for cfg in SYMBOLS:
        market = cfg["market"]
        cap = MAX_CONCURRENT_POSITIONS.get(market)
        was_open = is_in_position(cfg["symbol"], market, cfg["strategy_name"], cfg["capital"])
        allow_entry = cap is None or open_counts.get(market, 0) < cap

        report, event, is_entry = advise(**cfg, allow_entry=allow_entry)
        print(report)
        print()
        if event:
            (entry_reports if is_entry else other_event_reports).append(report)
            is_open_now = is_in_position(cfg["symbol"], market, cfg["strategy_name"], cfg["capital"])
            if is_open_now and not was_open:
                open_counts[market] = open_counts.get(market, 0) + 1
            elif was_open and not is_open_now:
                open_counts[market] = max(0, open_counts.get(market, 0) - 1)

    for report in entry_reports:
        send_discord_message(header + "\n\n" + report)

    if other_event_reports:
        send_discord_message(header + "\n\n" + "\n\n".join(other_event_reports))

    total_events = len(entry_reports) + len(other_event_reports)
    if total_events:
        print(f"Discord notified — {len(entry_reports)} entry (individual msgs) + {len(other_event_reports)} other event(s) this run.")
    else:
        print("No events this run (all HOLD/WAIT) — Discord not notified.")

    record_heartbeat()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
