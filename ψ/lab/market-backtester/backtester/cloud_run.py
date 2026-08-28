"""Cloud cron entrypoint: loops multiple symbols through `advise()` in one run and posts
ONE Discord message combining only the symbols that had a real event this check (entry,
exit, or stop/target hit) — HOLD/WAIT results are still printed to the log but don't
trigger a notification, so running this more often doesn't mean more Discord noise.

Usage: python -m backtester.cloud_run
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

BANGKOK_TZ = ZoneInfo("Asia/Bangkok")

from .advisor import advise, is_in_position
from .config import MAX_CONCURRENT_POSITIONS
from .notify import send_discord_message, send_discord_message_to_channel
from .trade_store import record_heartbeat
from . import sentiment

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
    header = f"=== {datetime.now(BANGKOK_TZ).strftime('%Y-%m-%d %H:%M:%S')} ICT ==="
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

    # Every ENTER and EXIT goes out as its own Discord message with an @mention — both are
    # real decision windows for anyone holding a matching real position (2026-08-21: a
    # TAKE-PROFIT exit was originally batched/unmentioned as "informational only," which
    # was wrong — missing a sell signal is just as costly as missing a buy one). A reaction
    # also only has ONE message to attach to, so two events sharing a message would be
    # unresolvable for the quick-confirm flow anyway. There are no other event types —
    # advise() only ever flips `event` True on an entry or an exit.
    urgent_reports = []
    crypto_signal_now: dict[str, int] = {}  # symbol -> this run's technical signal, for the sentiment overlay below
    for cfg in SYMBOLS:
        market = cfg["market"]
        cap = MAX_CONCURRENT_POSITIONS.get(market)
        was_open = is_in_position(cfg["symbol"], market, cfg["strategy_name"], cfg["capital"])
        allow_entry = cap is None or open_counts.get(market, 0) < cap

        result = advise(**cfg, allow_entry=allow_entry)
        print(result.report)
        print()
        if market == "crypto":
            crypto_signal_now[cfg["symbol"]] = result.signal_now
        if result.event:
            urgent_reports.append(result.report)
            is_open_now = is_in_position(cfg["symbol"], market, cfg["strategy_name"], cfg["capital"])
            if is_open_now and not was_open:
                open_counts[market] = open_counts.get(market, 0) + 1
            elif was_open and not is_open_now:
                open_counts[market] = max(0, open_counts.get(market, 0) - 1)

    for report in urgent_reports:
        send_discord_message(header + "\n\n" + report, mention_owner=True)

    total_events = len(urgent_reports)
    if total_events:
        print(f"Discord notified — {total_events} event(s) this run (each its own @mentioned message).")
    else:
        print("No events this run (all HOLD/WAIT) — Discord not notified.")

    # Thai news sentiment overlay (2026-08-27) — a broken scrape or a flaky LLM call must
    # never take down the actual trading-signal loop above, so it's fully isolated here:
    # any exception is caught, logged, and swallowed rather than propagated.
    try:
        overlay_lines = sentiment.run_overlay(crypto_signal_now)
        sentiment_channel_id = os.environ.get("SENTIMENT_CHANNEL_ID")
        if overlay_lines and sentiment_channel_id:
            digest = header + "\n\n📰 ข่าว sentiment overlay\n_ไม่ใช่คำแนะนำการลงทุน — โปรดตรวจสอบก่อนตัดสินใจ_\n\n" + "\n\n".join(overlay_lines)
            send_discord_message_to_channel(digest, sentiment_channel_id)
            print(f"Sentiment overlay — {len(overlay_lines)} item(s) sent to SENTIMENT_CHANNEL_ID.")
        elif overlay_lines:
            print(f"Sentiment overlay — {len(overlay_lines)} item(s) found but SENTIMENT_CHANNEL_ID not set, not sent.")
        else:
            print("Sentiment overlay — nothing new/aligned this run.")
    except Exception as e:
        print(f"Sentiment overlay failed (non-fatal, trading loop unaffected): {e}", file=sys.stderr)

    record_heartbeat()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
