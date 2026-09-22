# Handoff: Grok Live Watch — read-only client built, tested, live-verified

📡 Session: 2d5ed472 | ayami-oracle | ~7.5h (continuation of 2026-09-22_19-05 handoff, same task)

**Date**: 2026-09-22 19:18
**Context**: ~246k (very long — this session must end now)

## Context
**Oracle**: Ayami Oracle (หญิง) | **Human**: มอส (ชาย)
**Mode**: Fast | **Memory**: Auto

## What We Did (since the 19:05 handoff)

- Confirmed Binance TH's real REST API shape by grepping the **raw HTML** of
  `https://www.binance.th/api-docs/en/` directly (not trusting only an AI-summarized fetch):
  base URL `https://api.binance.th`, `X-MBX-APIKEY` header, HMAC-SHA256 signing over the
  urlencoded query string, `/api/v1/...` paths (not Binance.com's `/api/v3/...`).
- Wrote `ψ/lab/grok-live-watch/live_watch/config.py` + `live_watch/client.py` — a **GET-only**
  client (`server_time`, `account`, `open_orders`, `all_orders`, `user_trades`). No
  order-placing/cancelling/withdrawal method exists anywhere in the module.
- Wrote `tests/test_client.py` — 7 tests, all passing: independent HMAC reference check,
  header/param verification, rate-limit(429)/ban(418) handling, and a guard test
  (`test_client_defines_no_write_capable_methods`) that fails loudly if a future edit ever adds
  a write-capable method to the class.
- Set up `.venv` + `requirements.txt` (`requests`, `python-dotenv`), ran the tests — all green.
- **Live-verified end-to-end** against the real API with มอส's real key: `server_time()` (public,
  clock drift only 51ms) and `account()` (signed) both succeeded — 12 assets returned.
- Hit and resolved a **false alarm**: `accountV2`'s `canTrade`/`canWithdraw`/`canDeposit` fields
  read `true` even after มอส "fixed" the key permissions — turned out these are **account-level**
  flags, not the calling key's own scope (Binance TH has no `apiRestrictions`-equivalent
  endpoint, unlike Binance.com). Corrected in-session, documented in the project README and
  memory so it's not re-triggered next time. No actual security issue was found or created here.

## Pending — carried forward

- [ ] Position/P&L/alert polling logic: poll `account()` / `open_orders()` / `user_trades()` on
      a schedule, diff against last-seen state to detect new fills/closes.
- [ ] Compare live positions/signals against treade's frozen strategy snapshot (in the README)
      to produce the "signal/strategy analysis" มอส actually asked for — this is the part that
      replaces Grok Bot's own token spend, not yet started.
- [ ] Discord notify wiring — reuse `DISCORD_BOT_TOKEN`/`REPORT_CHANNEL_ID`, pattern from
      `ψ/lab/grok-crypto-paper-trading/paper_trading/notify.py`.
- [ ] Local cron/launchd scheduling.
- [ ] More tests once polling/notify logic exists.
- [ ] Re-export treade's strategy snapshot periodically (it can drift from what's live).

## Cleanup noticed (not this session's work — leave alone unless มอส asks)

Same as the 19:05 handoff: concurrent session(s) left `ψ/inbox/focus-agent-*.md`,
`ψ/memory/learnings/session-metrics.md`, `ψ/outbox/2026-09-22_pending.md` modified and a few
unrelated `ψ/memory/learnings/` + `ψ/memory/retrospectives/` files untracked (eVisa video-OCR
task). Several stale worktrees still present. Check `maw peek` before touching any of it.

## Key Files

- `ψ/lab/grok-live-watch/README.md` — full design, boundaries, confirmed API shape, strategy
  snapshot, both incident write-ups (secrets exposure + false alarm), current status
- `ψ/lab/grok-live-watch/live_watch/client.py` + `config.py` — the working, tested client
- `ψ/lab/grok-live-watch/tests/test_client.py` — 7 passing tests
- `ψ/lab/grok-live-watch/.env` — real key, gitignored, already verified present/correct format
- `~/.claude/projects/-Users-phongcheatphus-ayami-oracle/memory/project_grok_live_watch.md` —
  full memory, more detail than this handoff
- Sibling refs: `ψ/lab/grok-crypto-paper-trading/paper_trading/notify.py` (Discord pattern to
  reuse), `ψ/lab/market-backtester/` (Discord bot/channel env vars, deploy pattern)

## Next session: start here

1. `/recap` to load this handoff.
2. `cd ψ/lab/grok-live-watch && source .venv/bin/activate` (venv + deps already installed).
3. Design the polling/diff + signal-analysis logic (this is the actual value-add over Grok
   Bot's own reporting — don't skip straight to Discord wiring before this exists).
4. Then Discord notify, then scheduling.
