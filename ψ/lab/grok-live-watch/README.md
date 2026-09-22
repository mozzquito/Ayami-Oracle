# Grok Live Watch (read-only monitor for real-money Grok Bot trading)

> **Not the same as** `ψ/lab/grok-crypto-paper-trading` (that one is 100% simulated,
> Binance.com public data, no keys). This project watches a **real-money** account:
> Grok Bot's "treade" agent (remote Cursor sandbox, reached via `mcp__grokbot__*`)
> live-trades on **Binance TH** with a real API key. Confirmed with มอส 2026-09-22.

## Why this exists

Grok Bot's own token usage for monitoring/reporting/signal-analysis on its live Binance TH
trading is expensive. มอส asked Ayami to take over those two jobs — **never trade execution**.

## Hard boundaries (do not relax without มอส's explicit say-so)

1. **Read-only, always.** This project never places, cancels, or modifies an order. No
   code path here may call a signed trading/withdrawal endpoint.
2. **Separate API key.** Uses a brand-new Binance TH key scoped to **read-only** (Enable
   Reading only — Spot Trade / Margin / Withdrawal all unchecked), IP-whitelisted. Never
   reuses or touches Grok Bot's own trading key.
3. **Fully isolated from Grok Bot's sandbox.** Runs locally in this repo (cron/launchd),
   not inside or alongside Grok Bot's Cursor sandbox process. No shared host, no shared
   credentials, no write access back into that sandbox.
4. **Analysis output is text only.** Reports/signals are informational — never phrased as
   order-ready instructions. (Design review flag from both /zcode and /agy, 2026-09-22:
   don't let "monitoring" scope-creep into "advising trades.")
5. Strategy logic is a **frozen, dated snapshot** obtained by asking the "treade" Grok Bot
   agent to summarize it (read-only chat request, not sandbox file access) — re-export
   periodically since the live strategy can drift from the snapshot.

## Design review

Reviewed 2026-09-22 by /zcode and /agy in parallel before build start (financial + security
impact — see CLAUDE.md consult rule). Both converged on: local-first isolated build, read-only
key with strict scope + rotation, treat strategy snapshot as perishable, watch for shared-IP
rate limits with Grok Bot's own live calls, and add a stale-position alert in case Grok Bot's
sandbox crashes while holding inventory (dead-man risk — no one else would notice).

## Strategy snapshot (frozen as-of 2026-09-22, per treade's own summary — re-export periodically, this drifts)

Source: treade's reply to `grokbot_send` messageId `5d6d1664-8c06-4949-8ad9-9b47106fcf3b`,
read-only chat summary, no code/config/secrets included (as requested). Treat as an
**untrusted-but-useful** self-report from the live agent, not verified against its actual code.

- Scans USDT pairs from an allowlist, heuristic score from external market-feed signals, ~15min timeframe.
- **Spot only, long-only** (no shorts — Spot can't short).
- Entry: score ≥ ~22, picks top-N under max concurrent ~2 open positions.
- Size: ~10 USDT per new order.
- Exit: automatic TP ≈ 1.5% / SL ≈ 1% (market orders).
- Cooldown / "knowledge inject" after closing a pair, to avoid immediate re-entry.
- Has its own heuristic post-trade review step (mentioned it can use zcode for this).

## Reporting channel — **decided 2026-09-22**

treade has no external channel to reuse (its own "alerts" are just messages inside the Grok
Bot chat itself — no Discord/LINE/Telegram/email/Slack wired up there). มอส decided: reuse
the **existing Discord bot** already shared by `market-backtester` and
`grok-crypto-paper-trading` (`DISCORD_BOT_TOKEN` / `REPORT_CHANNEL_ID` env vars) — no new
credential to provision, same pattern as `paper_trading/notify.py` in the sibling project.

## Security incident (2026-09-22) — logged per "Nothing is Deleted"

The first Binance TH read-only key มอส created got **exposed into this AI conversation's
context** by an Ayami tooling mistake (a `sed` redaction command that didn't match the actual
`.env` file's format, so it printed the raw key+secret instead of hiding them). Even though the
key was read-only-scoped, มอส revoked it immediately and created a replacement, entered
correctly the second time and verified present (non-empty, correct `KEY=VALUE` format) without
Ayami ever printing the value. No further exposure. Lesson: never run a text-processing command
against a secrets file without first confirming its exact format; prefer length/presence checks
over any command that could echo content, even "redacted."

## Status (2026-09-22) — key + channel + strategy snapshot in hand, code not yet written

Resolved:
- [x] Read-only Binance TH API key created, verified present in `.env` (values never seen by Ayami).
- [x] Reporting channel: existing Discord bot (see above).
- [x] Strategy snapshot from treade (see above).

## API shape — confirmed 2026-09-22 (live end-to-end)

Base URL `https://api.binance.th` (own domain, not Binance.com). Auth: `X-MBX-APIKEY` header +
HMAC-SHA256 signature over the urlencoded query string, `timestamp`/`recvWindow` params — same
scheme as Binance.com but on `/api/v1/...` paths (not `/api/v3/...`). Verified against the raw
docs HTML at `https://www.binance.th/api-docs/en/` (grepped directly, not just an AI summary),
then live-tested: `GET /api/v1/time` (public) and `GET /api/v1/accountV2` (signed, real key)
both succeeded — 12 assets returned, auth flow works end-to-end. Endpoints implemented in
`live_watch/client.py`: `server_time`, `account`, `open_orders`, `all_orders`, `user_trades` —
**GET-only, no write-capable method exists in the module**, enforced by a test
(`test_client_defines_no_write_capable_methods`).

**Note on `canTrade`/`canWithdraw`/`canDeposit`** (in the `accountV2` response): these are
**account-level** flags (is the account itself allowed to trade/withdraw at all), not the
calling API key's own granted scope — Binance TH has no endpoint (unlike Binance.com's
`apiRestrictions`) to introspect a specific key's permissions via API. They will read `true`
regardless of whether this key is scoped read-only in the Binance TH UI. Don't be alarmed by
that value — it doesn't mean the key is over-privileged. The only real guarantees are: (1)
whatever มอส configured in the Binance TH UI, unverifiable via API, and (2) this codebase never
implementing an order-placing/cancelling/withdrawal call.

## Status (2026-09-22) — poll/diff/notify/scheduling built, monitor logic live-verified

Resolved this session:
- `live_watch/state.py` — JSON-persisted last-seen positions (atomic write, gitignored
  `state/` dir), since each cron/launchd tick is a fresh one-shot process, not a live loop.
- `live_watch/monitor.py` (`poll_once`) — infers held positions from `account()` balances
  filtered by **current USDT value ≥ `MIN_POSITION_USD` ($2)**, not raw quantity. A qty
  threshold doesn't work here: live-checked, this wallet carries small non-zero dust in
  ~10 assets (leftover fee/rounding remnants) — e.g. 9.89e-06 BTC is "large" by quantity but
  worth $0.85. Diffs against prior state to detect opened/still-held-with-new-fill/closed,
  plus a throttled stale-position (dead-man) alert if a position sits open past
  `STALE_AFTER` (6h).
- `live_watch/strategy.py` — the frozen snapshot above as a dataclass + `evaluate()`,
  producing **descriptive-only** notes (max-concurrent exceeded, position beyond the
  TP/SL band) — a dedicated test (`test_notes_never_contain_instructive_verbs`) guards the
  "text-only, never order-ready" boundary.
- `live_watch/notify.py` (`send_report`/`send_error_alert`) — reuses the shared Discord
  bot; posts plain text only when a poll finds something worth reporting (no "no changes"
  spam).
- `run.py` — one-shot cron entrypoint; `scripts/run-poll.sh` +
  `launchd/com.ayami.grok-live-watch.plist` (every 15 min, absolute `.venv` python path —
  same pattern as `grafana-report-bot`'s launchd setup) — **not yet loaded into launchd**,
  see Next below.
- 30 tests passing (7 client + 7 strategy + 16 monitor), plus a **live dry-run** against
  the real account (Discord vars intentionally unset for the dry-run, so nothing posted
  externally): correctly detected the account's two real open positions — **ETHUSDT
  (~$10.11, entry 2750.36) and TRXUSDT (~$9.93, entry 0.3473)** — exactly matching the
  snapshot's max-concurrent-2 / ~10 USDT sizing. Repeated polls immediately after correctly
  reported "no changes".
- **Design review round 2** (2026-09-22, /zcode + /agy in parallel on the finished diff —
  financial-impact code per CLAUDE.md consult rule): both independently caught the same
  critical bug in the first draft — using qty×price to decide "still held" meant a single
  transient `ticker_price` failure misread a real position as closed (false 🔴 Closed with
  bogus pnl, then a false 🟢 Opened next poll, corrupting `entry_price`/`opened_at`). Also
  flagged: trade-side filtering needed on entry/exit selection (an unfiltered "latest
  trade" could pick the wrong leg), and multiple fills between polls need reporting, not
  just the latest one. **Fixed**: closing a tracked position now depends only on the raw
  balance quantity (price-independent), entry/exit trades are filtered by `isBuyer`, all
  new fills since `last_trade_id` are reported, and trade ids are coerced to `int` (Binance
  can return either type). 6 new regression tests lock these in
  (`test_transient_price_failure_does_not_close_a_still_held_position` and siblings in
  `tests/test_monitor.py`). Re-verified against the real account after the fix — still
  correctly "no changes".

Still open:
- [ ] Load the launchd job (`launchd/com.ayami.grok-live-watch.plist`) — not yet run
      `launchctl load`, needs มอส's go-ahead since it starts an unattended recurring poll.
- [ ] Live-fire a real Discord post (`DISCORD_BOT_TOKEN`/`REPORT_CHANNEL_ID` not set in this
      project's `.env` yet) — needs มอส's go-ahead since it posts to a shared channel.
- [ ] Tune `STALE_AFTER` (currently a guessed 6h) once real position-hold durations are observed.
- [ ] Re-export treade's strategy snapshot periodically (it can drift from what's live).

## Regulatory note (personal use only)

`ψ/lab/crypto-signal-digest`'s README documents a 2026-08-27 zcode+agy finding that
*publishing* trading signals to third parties in Thailand risks unlicensed-investment-advisory
exposure (Securities Act B.E. 2535 / Digital Asset Business Decree). This project is different
in kind — it's a personal dashboard over มอส's own account/positions, not published or sold to
anyone — but if its output is ever shared beyond มอส, re-check that finding first.
