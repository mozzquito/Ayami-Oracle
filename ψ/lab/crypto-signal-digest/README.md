# Thai Crypto/Trading Signal Digest — Prototype

Thai financial news → sentiment analysis → technical-indicator alignment → Discord digest.
Side-income idea #4 from [`ψ/writing/side-income-playbook.md`](../../writing/side-income-playbook.md).

## ⚠️ Regulatory risk — read this before doing anything with real customers

The requirement review (zcode + agy, 2026-08-27) found that publishing "trading signals" /
"HIGH CONVICTION" buy-sell alerts to **paying** subscribers in Thailand likely falls under
**unlicensed investment advisory** (Securities Act B.E. 2535) and potentially the **Digital Asset
Business Decree** for crypto-specific signals — both carry real (including criminal) liability
without an SEC Thailand license. Both agents recommended repositioning as "news + sentiment
aggregation" with no actionable language, and consulting a Thai securities lawyer before opening
any paid tier.

**มอส's explicit decision (2026-08-27): proceed with the original plan as-is, "HIGH CONVICTION"
wording included, risk accepted knowingly.** This prototype is built to that instruction. It is
**not wired to accept payment or open subscribers** — per the plan's own step 5, this stays a
personal paper-trade validation tool until accuracy is proven, which is also the point at which
the legal question stops being deferrable.

## Setup

1. `scripts/setup-wizard.sh` walks through NewsAPI/Firecrawl/TAAPI signup + Discord bot invite.
   OpenRouter and the Discord bot token are reused from the `realestate-video` and `discord-bot`
   projects respectively (same accounts) — no new signup needed for those two.
2. `npm install`
3. `npm run run -- --dry-run` (prints signals instead of posting) or `npm run run` (posts to Discord)

## What's actually verified (2026-08-27) vs. what's still assumed

Docs for TAAPI turned out to be stale/redirected (the old `api.taapi.io` endpoint from its own
"Get started" page 401'd on every auth variant tried); the real current API was found by following
the docs' own redirect to `docs.taapi.io` and confirmed live.

| Step | Service | Status |
|---|---|---|
| News scraping | Firecrawl | ✅ **Fully verified live**, end-to-end, repeatedly. Caught and fixed 2 real bugs in the process: `moneychannel.co.th` doesn't resolve at all — turns out the station **shut down** (real news, not a broken link), replaced with Thairath Money; `set.or.th`'s news page is a JS-rendered SPA that Firecrawl's basic scrape can't get past the shell of — dropped for now (see Known gaps). |
| Technical indicators | TAAPI.io | ✅ **Fully verified live** — RSI and MACD both confirmed for BTC/USDT with real current values, once the real `v2.taapi.io/indicator/<name>` endpoint (Bearer auth, `timeframe` param) was found. |
| Sentiment analysis | OpenRouter/DeepSeek | ✅ **Fully verified live** — batch-classified 10 real Thai headlines correctly (positive/neutral, sensible reasons). Not yet stress-tested against the double-negative Thai phrasing risk zcode's review flagged (e.g. "ขาดทุนลดลง" = recovering, not worsening) — the prompt tells the model to watch for this, but no adversarial test case has been run yet. |
| Delivery | Discord | ✅ **Fully verified live** — real digest posted to a real channel. Hit a real setup snag worth knowing about: the first "channel ID" given was actually a **server ID** (guild), not a channel ID — `Unknown Channel` from the API was the tell. Decoded the bot's own client ID from its token to generate a ready invite link rather than sending it hunting through the Developer Portal. |
| Indicator *alignment* ("HIGH CONVICTION" logic) | — | ⚠️ **Code path not yet exercised on real data** — no crypto-mentioning headline showed up in any live test run so far, so `conviction()` in `pipeline.ts` has never actually fired true on a real signal. Logic is simple and reviewed, but genuinely untested end-to-end. |

## Known gaps not yet decided (from the zcode + agy requirement review)

- **Regulatory** — see the box at the top. Not resolved, deliberately deferred per มอส's own instruction, but it doesn't go away.
- **NewsAPI.org kept but not load-bearing** — live-tested and found to have **zero coverage** of the named Thai financial sources (kaohoon.com/set.or.th/moneychannel.co.th all returned 0 articles even before moneychannel turned out to be dead). `NEWSAPI_KEY` is optional in `config.ts` and unused in the pipeline; Firecrawl direct-scraping replaced it as the real news source.
- **set.or.th not integrated** — real, valuable source (official SET news) but needs Firecrawl's JS-wait/interaction options or a different scraping approach to get past the SPA shell. Worth revisiting since it's the single most authoritative Thai market-news source.
- **Accuracy protocol undefined** — zcode's review flagged this specifically: "55-60% accuracy" needs a written definition (which timeframe, direction-only vs. magnitude, how outcomes get tracked) *before* the plan's own 1-week paper-trade validation starts, not after.
- **No scheduling wired up** — this is a manual/cron-callable CLI (`npm run run`), not yet running on a 15-minute loop. Intentionally deferred until the pipeline itself proves worth automating.
- **NewsAPI.org free-tier math** (from the original review, now moot since NewsAPI isn't load-bearing) — kept here as a reminder in case NewsAPI is ever reintroduced: 15 sources × 96 polls/day would blow the 100 req/day free limit on day one.

## Files

- `src/news.ts` — Firecrawl scraping of Thai finance sites, markdown-link extraction
- `src/sentiment.ts` — OpenRouter/DeepSeek batch sentiment classification (structured JSON out)
- `src/indicators.ts` — TAAPI.io RSI/MACD lookup for watched crypto pairs
- `src/store.ts` — SQLite storage (WAL mode), dedup via `url UNIQUE`, tracks what's been sent
- `src/discord.ts` — one-shot digest sender, reuses `ψ/lab/discord-bot`'s bot token/pattern
- `src/pipeline.ts` — CLI entry point, runs one full poll cycle
- `scripts/setup-wizard.sh` — interactive account/API-key setup (run once)
