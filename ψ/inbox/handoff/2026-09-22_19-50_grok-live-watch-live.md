# Handoff: Grok Live Watch — LIVE (launchd loaded), one item unverified

**Date**: 2026-09-22 19:50
**Context**: ~170k (past warn threshold — this session should end now, see `/forward`)

## Context
**Oracle**: Ayami Oracle (หญิง) | **Human**: มอส (ชาย) | **Mode**: Fast

## What happened this session (continuation of 19:18 handoff)

1. Built `live_watch/state.py` (JSON position-diff state), `strategy.py` (frozen snapshot +
   text-only `evaluate()`), `monitor.py` (`poll_once` — infers positions from balance USD
   value ≥$2, not raw qty), `notify.py` (Discord), `run.py` (cron entrypoint),
   `scripts/run-poll.sh` + `launchd/com.ayami.grok-live-watch.plist` (15min interval).
2. **zcode + agy design review** (financial-impact code, parallel consult) both caught the
   same critical bug: using qty×price to decide "still held" made a transient
   `ticker_price` failure misreport a real position as closed. **Fixed**: close detection
   now uses raw balance qty only (price-independent); entry/exit trade selection filters
   by buy/sell side; all fills since `last_trade_id` reported, not just latest; ids
   coerced to `int`. 6 regression tests added (30 total, all passing).
3. Live-verified against the real account repeatedly — correctly found ETHUSDT (~$10.11)
   + TRXUSDT (~$9.93) as the two real open positions, correctly reported "no changes" on
   repeat polls, both before and after the bugfix.
4. มอส approved going live. Copied `DISCORD_BOT_TOKEN` from
   `ψ/lab/crypto-signal-digest/.env` into `ψ/lab/grok-live-watch/.env`, and copied that
   file's `DISCORD_CHANNEL_ID` in as `REPORT_CHANNEL_ID` — มอส confirmed explicitly this is
   the *same* channel intentionally (crypto-signal-digest and grok-live-watch share one
   Discord channel). Neither value was ever printed — copied via shell redirection, only
   presence/count checked afterward.
5. `launchctl load launchd/com.ayami.grok-live-watch.plist` succeeded —
   `launchctl list | grep grok-live-watch` shows `com.ayami.grok-live-watch` registered.
   **It is now polling live every 15 minutes.**

## Open / unverified

- [ ] **A real Discord post has never actually been confirmed to land.** The one attempt
      to send a clearly-labeled `[TEST]` message was blocked by Claude Code's auto-mode
      permission classifier ("External System Writes" — a deliberate safety gate, not a
      bug; did not attempt to route around it). Since the account's positions haven't
      changed, no real poll has had anything to post yet either. **Next session (or มอส
      directly) should either**: (a) watch `ψ/lab/grok-live-watch/logs/poll.log` next time
      a position actually opens/closes/fills to confirm a post went out, or (b) มอส runs a
      manual test send themselves (`cd ψ/lab/grok-live-watch && source .venv/bin/activate
      && python -c "from live_watch.notify import send_report; print(send_report('[TEST] ignore'))"`)
      since Claude can't past the classifier.
- [ ] `STALE_AFTER` (6h dead-man threshold) is a guess, untuned against real hold durations.
- [ ] Re-export treade's strategy snapshot periodically (documented as drifting).
- [ ] `logs/` dir exists but launchd hasn't fired yet at handoff time (first tick ~15min
      after load) — worth a first check that `poll.log` is actually being written to.

## Key files

- `ψ/lab/grok-live-watch/README.md` — full status, both design-review rounds, incidents
- `ψ/lab/grok-live-watch/live_watch/monitor.py` — the poll/diff logic (read the module
  docstring — it explains the false-close bug and fix in detail)
- `~/.claude/projects/-Users-phongcheatphus-ayami-oracle/memory/project_grok_live_watch.md`
- `ψ/lab/grok-live-watch/logs/poll.log` — check this first next session

## Next session: start here

1. `/recap` to load this handoff.
2. Check `ψ/lab/grok-live-watch/logs/poll.log` exists and has entries (confirms launchd is
   actually firing).
3. Confirm a Discord post landed once a real position event occurs, or have มอส send the
   manual test above.
4. If both check out, this project is essentially done — only ongoing maintenance
   (STALE_AFTER tuning, strategy re-export) remains.
