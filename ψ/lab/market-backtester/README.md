# market-backtester

Python CLI for market analysis + rule-based strategy backtesting. Single-asset, long-only, daily timeframe. Covers SET (Thai stocks), US/global stocks, crypto, and forex through one data source (yfinance).

Grounded in techniques from *Deep Learning for Finance* (Sofien Kaabar, O'Reilly 2024) — see `ψ/learn/books/deep-learning-for-finance-sofien/` for the source material (Ch. 11 indicator strategies, Ch. 12 risk management/position sizing).

## Install

```bash
cd ψ/lab/market-backtester
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Thai stock (SET) — bare symbol gets .BK appended automatically
python -m backtester run --symbol PTT --market set --strategy sma_cross --params "fast=20,slow=50" --start 2020-01-01

# US stock
python -m backtester run --symbol AAPL --market us --strategy rsi_threshold --params "window=14,oversold=30,overbought=70" --start 2021-01-01

# Crypto
python -m backtester run --symbol BTC --market crypto --strategy macd_cross --start 2022-01-01

# Forex
python -m backtester run --symbol EURUSD --market forex --strategy bollinger_bounce --params "window=20,num_std=2" --start 2021-01-01 --end 2024-01-01

# Book-grounded strategy (Ch.11 EURUSD example: RSI(5) + price vs SMA(20)) with Kelly sizing + stop/target (Ch.12)
python -m backtester run --symbol EURUSD --market forex --strategy book_rsi_ma \
  --sizing kelly --stop-pct 0.03 --target-pct 0.06 --start 2021-01-01 --end 2024-01-01

# List available strategies
python -m backtester list-strategies

# Twice-a-day check instead of watching charts: morning and evening, same command
python -m backtester advise --symbol EURUSD --market forex --strategy book_rsi_ma \
  --sizing kelly --stop-pct 0.03 --target-pct 0.06 --capital 100000

# How much capital do you need for --sizing fractional to be meaningful in this market?
python -m backtester min-capital --market forex --symbol EURUSD --stop-pct 0.03 --risk-pct 0.01
```

## Options

| Flag | Default | Meaning |
|---|---|---|
| `--capital` | 100000 | Starting cash |
| `--commission` | 0.001 | Fraction charged per trade (0.1%) |
| `--slippage` | 0.0 | Fraction of fill-price gap, applied on entry/exit |
| `--sizing` | fixed | Position sizing method: `fixed`, `fractional`, or `kelly` (see below) |
| `--size-pct` | 1.0 | `fixed` sizing: fraction of available cash deployed per entry |
| `--risk-pct` | 0.01 | `fractional` sizing: fraction of account risked per trade (needs `--stop-pct`) |
| `--stop-pct` | — | Stop-loss distance below entry, e.g. `0.05` = 5%. Required by `--sizing fractional` |
| `--target-pct` | — | Take-profit distance above entry, e.g. `0.10` = 10% |
| `--save-report path.md` | — | Write a markdown report + trade log |
| `--save-chart path.png` | — | Write an equity-curve chart (requires matplotlib) |

## Strategies (`--strategy`)

- `sma_cross` — long while fast SMA > slow SMA (`fast`, `slow`)
- `macd_cross` — long while MACD line > signal line (`fast`, `slow`, `signal`)
- `rsi_threshold` — enter when RSI < `oversold`, exit when RSI > `overbought` (`window`)
- `bollinger_bounce` — enter when price closes below the lower band, exit above the mid band (`window`, `num_std`)
- `book_rsi_ma` — long when short-window RSI > 50 **and** price is above its longer-window SMA (`rsi_window`=5, `ma_window`=20). Mirrors the RSI(5) + (Close − SMA20) feature pair used in the book's Ch. 11 EURUSD example, collapsed from an LSTM-regression input into a direct rule.
- `book_rsi_ma_mtf` — **current production strategy** (switched 2026-08-15). Same daily `book_rsi_ma` signal, gated by a weekly trend filter (`weekly_ma_window`=10): only long if price also closed the most recently *completed* week above its weekly SMA. zcode and agy both independently flagged multi-timeframe confirmation as the highest-value addition when asked to review the system; backtested head-to-head across all 9 watchlist symbols (2023–2026) before switching — improved 8 of 9 (BTC -5.8%→+43.2%, SOL +41.6%→+144.4%, TRX -16.9%→+52.7%, plus lower max-drawdown and ~30-50% fewer trades across the board), NEAR was the one symbol that got worse (-39.3%→-53.0%) and was switched over anyway per user's explicit call, accepting that tradeoff for portfolio-level improvement. Lookahead-tested explicitly (a synthetic same-week price spike proven not to leak backward into earlier days of that week) since resampling to weekly is an easy place to introduce a subtle bug.

### Clean-room ports from whchien/ai-trader (2026-08-17, not yet in production)

Explored `whchien/ai-trader` (GPL-3.0, Backtrader-based) via `/learn` at the user's request to
evaluate whether it was worth adopting — agy and zcode both independently concluded the full
framework isn't worth migrating to (production paper-trading system already exists; GPL-3.0 would
copyleft this codebase if code were copied directly; Backtrader itself is effectively unmaintained
since ~2015), but flagged its strategy *algorithms* as worth re-deriving. These 5 are clean-room
pandas reimplementations — read the algorithm from their source, wrote the formula fresh, never
copied their code — with any market-portability adaptations noted in each function's docstring in
`strategy.py`. All 5 passed the same lookahead test used for `book_rsi_ma_mtf` (spike a future
price, confirm past signal bars are byte-identical).

- `rsrs_trend` — RSRS (Resistance-Support Relative Strength): rolling OLS slope of High-on-Low over `period`=18 bars; long above `buy_threshold`=0.8, exit below `close_threshold`=0.5. **Stop/target tuned 2026-08-17**: `config.STRATEGY_STOP_TARGET_PCT` auto-fills `stop_pct`/`target_pct` = 0.025/0.05 (crypto) or 0.015/0.03 (forex) — half of `book_rsi_ma_mtf`'s distances — whenever `run`/`advise` don't get an explicit `--stop-pct`/`--target-pct`. This strategy trades far more often, so it's more stop-distance-sensitive; the tighter distance improved *both* return and drawdown together on the 9-symbol backtest (avg return +43.4%→+50.9%, avg max-drawdown -46.3%→-39.8%, worst single-symbol max-drawdown -81.1%→-65.8%) rather than trading one for the other. An explicit `--stop-pct`/`--target-pct` still overrides this.
- `adaptive_rsi` — RSI whose smoothing period shortens in high-volatility/fast markets and lengthens in calm ones, instead of a fixed window. Entry/exit on oversold/overbought crossovers plus extreme-reversal signals.
- `vcp_breakout` — Minervini's Volatility Contraction Pattern: breakout to a new high after a volume+price squeeze, confirmed by a 250-day uptrend and a narrow recent channel. Dropped the original's fixed `$2,000,000` dollar-volume filter (single-currency, doesn't generalize across this watchlist).
- `risk_averse` — multi-factor filter: low volatility + fresh 5-day high + above-average volume + narrow 60-day range, all four required to enter, exit once 2+ deteriorate. Replaced the original's fixed `>100,000 shares` volume floor with a relative check (5-day vs 20-day average volume) since share-count thresholds don't port to crypto/forex.
- `triple_rsi` — multi-timeframe RSI alignment (short/mid/long periods all agreeing) adapted from a portfolio-rotation strategy down to a single-symbol entry signal; this project's own correlation guard (`MAX_CONCURRENT_POSITIONS`) already covers the cross-symbol position-limiting the original did via monthly rebalancing.

**Backtest vs current production baseline** (2023–2026, same $10 capital / stop-target as each
symbol's live config), average return across all 9 watchlist symbols:

| Strategy | Avg return | Notes |
|---|---|---|
| `book_rsi_ma_mtf` (current prod) | +12.6% | baseline |
| `rsrs_trend` | +50.9% | *(with tuned stop/target, see above — was +43.6% at `book_rsi_ma_mtf`'s stop/target distance)*. High trade frequency (up to 366 trades/symbol on crypto), still the highest drawdown of the 5 (avg -39.8%, worst -65.8%) |
| `adaptive_rsi` | +35.4% | NEAR +261.7% is an outlier pulling the average up; forex legs only had 4 trades each (75% win rate, small sample) |
| `risk_averse` | +8.2% | few trades on some symbols, roughly baseline |
| `vcp_breakout` | +6.1% | fires rarely (needs 250-day uptrend + a squeeze pattern); 0 trades on 5 of 9 symbols this window |
| `triple_rsi` | +1.4% | underperforms baseline on this watchlist |

Not switched into `cloud_run.py` — these are new/unproven relative to `book_rsi_ma_mtf`'s one
day of live-equivalent validation, and `rsrs_trend`/`adaptive_rsi` in particular need a closer look
at drawdown and small-sample forex results before considering production use. Available now via
`--strategy rsrs_trend` etc. for further backtesting/experimentation.

## Position sizing (Ch. 12: "Risk Management Essentials")

- **`fixed`** — deploy `size_pct` of available cash on every entry. Simple, no stop required.
- **`fractional`** — "fixed fractional" from the book: risk `risk_pct` of the account on the distance to `--stop-pct`. Position size shrinks automatically as the stop gets wider.
- **`kelly`** — `f = P − Q/B` (win probability P, payoff ratio B = avg win / avg loss), reestimated from this run's own closed trades after `MIN_TRADES_FOR_KELLY` (10) of them exist; before that it uses a prior (50% win rate, 1.5 payoff ratio). Clipped to [0, 1] since v1 is long-only, no leverage.

`--stop-pct` / `--target-pct` behave as resting orders: from the bar *after* entry onward, each bar's Low/High is checked against the stop/target level before that bar's strategy signal is evaluated, so a stop can't fire on the same bar a position opened. Exit reason (`signal`, `stop`, or `target`) is recorded per trade in `--save-report`'s trade log.

## Design notes / assumptions (v1)

- **No lookahead**: signals are computed from each bar's close, then shifted one bar forward and filled at the *next* bar's Open — a strategy never trades on information from a bar it hasn't seen yet.
- **Single position only**: flat → long → flat. No shorting, no pyramiding, no multi-asset portfolios.
- **Annualization is asset-class-aware**: 252 trading days for US/SET stocks, 260 for forex, 365 for crypto (used in Sharpe/CAGR).
- **Commission is charged on both entry and exit**, slippage is an optional extra fraction applied to the fill price in the adverse direction.
- Ticker normalization: `--market set` appends `.BK`, `crypto` appends `-USD`, `forex` appends `=X`, `us` is passed through as-is — already-suffixed symbols are left unchanged.

## Advisory mode (`advise`) — check twice a day instead of watching charts

Run the same command in the morning and evening. It persists a small JSON position state per (symbol, market, strategy) under `.state/` (gitignored) and tells you what to do:

- **Not holding**: recommends ENTER (with computed size) if the strategy signal is bullish, or WAIT if not.
- **Holding**: checks the latest bar's Low/High against your stop/target first (same precedence as the backtest engine), then the strategy's own exit signal. Recommends HOLD, or EXIT with the reason (`stop`/`target`/`signal`).
- Never re-enters in the same check that just exited — mirrors the backtest engine's rule that a stop can't fire and refill on the same bar.
- Sizing math is the exact same function the backtest engine uses (`compute_entry_allocation`), so a strategy's live sizing matches what its backtest measured.
- `--reset` wipes the saved state and starts over with `--capital`.
- **This is a decision-support tool, not an execution engine** — no broker connection. It assumes you actually placed the trade it last recommended; if you didn't, `--reset` or hand-edit the JSON file in `.state/`.

## `min-capital` — how much money do you actually need?

Estimates the minimum account size for `--sizing fractional` to stay meaningful, from typical retail minimum trade sizes: forex micro lot (1,000 units), SET board lot (100 shares), 1 US share, ~$10 minimum notional for crypto. These are rule-of-thumb defaults, not your actual broker's numbers — confirm with them directly.

## Automated paper-trading loop (Railway cron — current)

Runs `python -m backtester.cloud_run` — loops **9 paper-trade positions** (no real money) through `book_rsi_ma_mtf`: BTC, ETH, SOL, TRX, BNB, NEAR (crypto) and EURUSD, GBPUSD, AUDUSD (forex), 24/7 in the cloud (doesn't depend on any local machine being on). Symbols were picked by actually running the strategy's live signal / historical return / % time bullish against real candidates and keeping the strongest — not guessed (see `ψ/memory/retrospectives/` or session history). Symbol list + params live in `backtester/cloud_run.py`'s `SYMBOLS`.

- **Project**: `market-backtester-advise` on Railway (`mozzquito's Projects` workspace) — **3 services** now: `market-backtester-advise` (the cron job), `market-backtester-dashboard` (live web dashboard, see below), `Redis` (shared trade history between them).
- **Schedule**: `deploy.cronSchedule` = `"0 1,7,13,19 * * *"` (01:00/07:00/13:00/19:00 UTC = 08:00/14:00/20:00/02:00 ICT — 4x/day). Railway cron: min 5-minute resolution, times not guaranteed to the minute.
- **State persistence**: a 500MB volume mounted at `/data`, `BACKTESTER_STATE_DIR=/data/.state` env var (see `advisor.py`) — one JSON file per symbol, holds live position state (in_position, entry price, stop/target). This volume is **exclusive to the cron service** — Railway volumes are single-service, which is why trade *history* (for the dashboard) goes through Redis instead (see below).
- **Discord notification is event-only**: `advise()` returns `(report, event)` — `event` is `True` only on a real entry/exit/stop/target this call, never on unchanged HOLD/WAIT. `cloud_run.py` collects just the event reports into one consolidated message and calls `backtester/notify.py` (pure Python, Discord REST API) directly — running more often doesn't mean more Discord noise.
- **Env vars on the cron service**: `DISCORD_BOT_TOKEN`, `REPORT_CHANNEL_ID` (same values as `../discord-bot/.env`), `BACKTESTER_STATE_DIR`, `PYTHONUNBUFFERED=1`, `REDIS_URL=${{Redis.REDIS_URL}}`.
- **Correlation guard** (added 2026-08-15, agy's suggestion after a zcode/agy roadmap review): `config.MAX_CONCURRENT_POSITIONS = {"crypto": 2, "forex": 2}`. The 6 crypto symbols move together often enough that a rally can fire 5+ entry signals in one run — that's one leveraged bet on "crypto goes up" wearing 5 costumes, not 5 independent ones. `advise(..., allow_entry=bool)` gates entries; `cloud_run.py` counts currently-open positions per market before the loop and keeps the count live as entries/exits happen *within* the same run, so a signal past the cap gets logged as blocked (visible in `railway logs`) but doesn't open a position or trigger a Discord ping.

**Two separate `railway.json` configs, one active file** — Railway's config-as-code reads whatever `railway.json` is in the directory at deploy time, and both services deploy from this same directory. `railway.cron.json` and `railway.dashboard.json` are the saved configs; copy the one you need over `railway.json` before deploying that service:

```bash
cd ψ/lab/market-backtester
railway status                              # project/services info
railway logs --lines 100 --service market-backtester-advise    # last cron run's output

# Redeploy the cron job (after editing backtester/cloud_run.py, advisor.py, etc.)
cp railway.cron.json railway.json && railway up --service market-backtester-advise

# Redeploy the dashboard (after editing dashboard.py)
cp railway.dashboard.json railway.json && railway up --service market-backtester-dashboard

# Trigger a cron run right now instead of waiting for the schedule: temporarily set
# "cronSchedule": null in railway.json, `railway up`, then restore + `railway up` again
```

**Known quirk (resolved)**: the *previous* service used a shell-piped `startCommand` (`advise | notify.py` as two separate processes) and `railway logs` never showed its stdout, even though the pipeline demonstrably ran correctly (proven via volume state-file timestamps). Switching to a single-process Python entrypoint (`cloud_run.py`, calling `notify.send_discord_message()` directly instead of piping to a second process) made logs show up normally — so this was specific to shell pipelines under Railway's log capture, not a real bug, and it's now moot since there's no pipe anymore.

**Known quirk (unresolved, worth knowing about)**: the original service (`470b61f1...`) started failing every build with `failed to solve: secret RAILWAY_GIT_REPO_OWNER not found` — a git-context error that shouldn't apply to a CLI-uploaded (non-GitHub-connected) service. It failed identically 4 times in a row before being abandoned; deleting the service and creating a fresh one in the same project (after `railway volume detach`/`attach` to preserve state) resolved it immediately. If a future deploy starts failing at the generic "install mise packages: python" build step with no relation to your own code changes, this same recreate-the-service workaround is the fastest fix.

**Known bug (critical — check this first if Discord ever goes quiet again)**: `railway up`'s config-as-code deploy does **not reliably propagate `deploy.cronSchedule` to the service's live scheduler**. The deployment succeeds, its own manifest (`fileServiceManifest.deploy.cronSchedule`) shows the correct value, `railway.json` on disk is correct — but the actual live `ServiceInstance.cronSchedule` field silently stays/reverts to `null`, so the cron never fires again. This is exactly what happened 2026-08-12→2026-08-15 (zero Discord notifications for 3 days, confirmed via `railway logs --since 72h` returning nothing). Upgrading the CLI did not fix it; toggling `cronSchedule` null→value→null→value via repeated `railway up` did not fix it either.

**The fix**: set it directly via the GraphQL API, bypassing `railway up` entirely:
```bash
railway api 'mutation($environmentId: String!, $serviceId: String!, $input: ServiceInstanceUpdateInput!) { serviceInstanceUpdate(environmentId: $environmentId, serviceId: $serviceId, input: $input) }' \
  --var environmentId=24ed59db-611e-4316-ad53-11dbf45a6531 \
  --var serviceId=a4ef9c2e-5ec1-41fa-b4b8-f7d92878776c \
  --var 'input={"cronSchedule":"0 1,7,13,19 * * *"}'
```
Verify it actually took (this is the one query that's ground-truth — `railway status`'s CLI display of this field cannot be trusted either):
```bash
railway api 'query($environmentId: String!, $serviceId: String!) { serviceInstance(environmentId: $environmentId, serviceId: $serviceId) { cronSchedule nextCronRunAt } }' \
  --var environmentId=24ed59db-611e-4316-ad53-11dbf45a6531 \
  --var serviceId=a4ef9c2e-5ec1-41fa-b4b8-f7d92878776c
```
A non-null `nextCronRunAt` in the response is the only reliable confirmation the schedule is actually live.

**Both defenses below shipped 2026-08-15, second-opinion-reviewed by zcode + agy (both independently recommended the same two-layer approach: fix at deploy time, watch at runtime):**

1. **`./deploy-cron.sh`** — the mandatory way to deploy this service from now on. Does `railway up` → force-set `cronSchedule` via the GraphQL mutation → verify `nextCronRunAt` is non-null → **exits 1 and refuses to claim success if it isn't**. Never deploy this service with plain `railway up` again; the whole point is that deploy alone can't be trusted.
2. **Heartbeat watchdog** — `cloud_run.py` calls `trade_store.record_heartbeat()` once at the end of every successful run (writes a Unix timestamp to Redis). The dashboard checks it on every page load: green caption if the last run was within 8h (2x the max gap between scheduled runs), a loud `st.error` banner if it's been silent longer than that, and a distinct warning if no heartbeat has ever been recorded at all. This is the layer that catches the *exact* failure mode that caused the 3-day silence — the schedule going dead silently sometime *between* deploys, which a deploy-time check alone can never see.

**Local launchd version**: removed in favor of Railway (per decision on 2026-08-11 — usage-based Railway cost accepted, local+cloud found more error-prone to keep in sync than just running one). `run_advise_paper.sh` and `../discord-bot/notify.mjs` are kept in the repo as reference/manual-trigger tools, not part of the active schedule.

## Quick-confirm real trades (Discord ✅/❌ reactions, 2026-08-17)

Boss asked whether the bot could auto-trade real money unattended — declined that specifically
(no broker API key ever gets held or used to place a real order; a human must always be the one
who actually executes on their own broker/exchange), but built the safe version of what that
request was really after: making the *human* step as fast as a tap instead of typing.

- Every fresh ENTER signal now posts as its **own** Discord message (not batched with other
  events) — a reaction can only attach to one message, so a signal needs a message all to
  itself to stay unambiguous. Exit/stop/target events (informational only, no action needed)
  still batch together as before.
- The message carries a 🔗 link straight to the right Binance trading pair for crypto symbols
  (`https://www.binance.com/en/trade/{SYMBOL}_USDT?type=spot` — a stable, documented part of
  Binance's own site routing, not a special API). **No equivalent exists for forex/Exness** —
  checked before building this (neither Binance nor MT4/MT5 publicly document a deep-link that
  pre-fills exact order price/quantity), so forex signals just get the plain numbers to enter
  manually in the Exness/MT5 app.
- The bot auto-adds ✅/❌ reactions to its own signal messages. Tapping ✅ logs "took this trade"
  to `moss-real-trades.md` (same file/format as typing `บันทึกเทรด`, plus mirrors to the
  dashboard's Execution Tracker via the existing webhook bridge); ❌ logs "skipped this signal" —
  both are pure logging, no broker ever touched.
- Parsing uses a machine-readable marker line embedded in the message
  (`[trade-signal:SYMBOL:market:entry=...:stop=...:target=...:size=...]`) rather than trying to
  regex the Thai prose — `advisor.py` emits it, `ψ/lab/discord-bot/bot.mjs` reads it back out.
- **What this deliberately does NOT do**: place any real order, hold any broker/exchange API
  credential, or remove the human from the loop. The whole design constraint was "make
  confirming fast, never make confirming optional."

## Live dashboard (`dashboard.py`, Railway service `market-backtester-dashboard`)

A Streamlit app showing live entry/exit signals for the same 9 symbols as the cron loop — independent of the cron's actual running position state (it recomputes each symbol's own strategy signal fresh from current data every load, same math, but doesn't touch `.state/`).

**Bug caught before shipping (2026-08-15)**: `load_symbol_data()` originally imported and called `book_rsi_ma` directly instead of looking up `cfg["strategy_name"]` from `STRATEGIES`. Harmless while only one strategy existed; would have silently shown the *wrong* signal the moment the cron switched to `book_rsi_ma_mtf`, since the dashboard would keep computing the old strategy while production ran the new one. Fixed to look up `STRATEGIES[strategy_name]` per symbol before the switch went live — worth remembering as a pattern: anywhere a value is duplicated instead of imported from the single source of truth (`cloud_run.py`'s `SYMBOLS`) is a place a future change can silently desync.

- **Overview table**: price, RSI(5), SMA(20), current signal, computed stop/target if entering now, and **% of days bullish over the trailing 6mo/12mo** (real computed number from yfinance history, not an estimate).
- **Detail view**: price+SMA(20) chart with bullish days marked, RSI(5) subplot with the 50 reference line.
- **Trade History section**: closed trades pulled from Redis (`backtester/trade_store.py`) — this is the one place that *does* show real executed paper-trades, since `advisor.py`'s exit path writes every closed trade to Redis in addition to the cron's own local volume state. Redis is what lets a *separate* Railway service (the dashboard) see trades from the cron service, since volumes can't be shared across services.
- **Execution Tracker section** (Paper entries vs. Real trades, side by side): the "did Boss actually follow the signal" comparison agy suggested (2026-08-15). Paper side is `trade_store.record_entry()`, called from `advisor.py`'s entry path, every time the strategy actually signals a LONG. Real side comes from a webhook bridge — see below. **Still manual eyeballing, not automated matching** — no attempt to algorithmically pair a paper entry with a real trade note; the two tables are just both sorted newest-first so a human can compare them.
- **`/api/log-real-trade` webhook** (the local↔cloud bridge): `moss-real-trades.md` is local-only on Boss's Mac (gitignored, no sync anywhere); Redis is Railway-private-network-only (deliberately not exposed publicly — same call as skipping SSH key registration earlier). Rather than expose Redis directly, `server.py` wraps the dashboard in `st.App(..., routes=[...])` (Streamlit's ASGI mode — see `streamlit docs st.App`) and adds one authenticated POST route. `ψ/lab/discord-bot/bot.mjs`'s `appendTradeEntry()` POSTs the same text it just wrote locally (plus a loose keyword-guessed `symbol_hint`, never a parsed number) to this route after every `บันทึกเทรด`/`เทรดจริง` message. Auth is a single shared bearer token (`TRADE_LOG_WEBHOOK_TOKEN`, same value on both the dashboard's Railway env and the local `.env`) — a personal single-writer webhook, not a public API, but still checked on every request (401 on missing/wrong token, never silently accepted). Best-effort on the bot side: a webhook/network failure never blocks or reverts the local file write.
- **Cron heartbeat status**: banner at the top of the dashboard — green if the cron ran within the last 8h, red if it's gone silent longer than that (the exact failure mode from the 2026-08-12→15 incident). See "Known bug" above.
- **Run locally**: `uvicorn server:app --port 8501` (not `streamlit run` anymore — that would skip the webhook route; needs `streamlit`, `plotly`, `uvicorn` — already in `requirements.txt`). Local runs won't see Redis trade history unless `REDIS_URL` is set in your shell — this is a cloud-only integration by default.
- **Public URL**: `https://market-backtester-dashboard-production.up.railway.app`
- **Port note**: `startCommand` uses `--port $PORT` (Railway injects this — came out to 8080 at deploy time). The service's public domain must target whatever `$PORT` actually resolves to — check `railway logs --service market-backtester-dashboard` for the "Uvicorn running on http://0.0.0.0:XXXX" line if the domain ever 502s, and `railway domain update <domain> --port <that number> --service market-backtester-dashboard`.

## Known quirks

**Resolved — piped shell command hid logs**: the *original* cron service used a shell-piped `startCommand` (`advise | notify.py` as two separate processes) and `railway logs` never showed its stdout, even though the pipeline demonstrably ran correctly (proven via volume state-file timestamps). Switching to a single-process Python entrypoint (`cloud_run.py`, calling `notify.send_discord_message()` directly instead of piping to a second process) made logs show up normally — so this was specific to shell pipelines under Railway's log capture, not a real bug.

**Resolved — stuck service build**: the original cron service (`470b61f1...`) started failing every build with `failed to solve: secret RAILWAY_GIT_REPO_OWNER not found` — a git-context error that shouldn't apply to a CLI-uploaded (non-GitHub-connected) service. It failed identically 4 times in a row before being abandoned; deleting the service and creating a fresh one in the same project (after `railway volume detach`/`attach` to preserve state) resolved it immediately. If a future deploy starts failing at the generic "install mise packages: python" build step with no relation to your own code changes, this same recreate-the-service workaround is the fastest fix.

**Not fully verified — Redis round trip**: `trade_store.py`'s write path (cron service → Redis on a trade close) hasn't been observed with a *real* closed trade yet as of this writing — all 9 positions were still open at deploy time. The read path and graceful-no-op path are both verified locally. Will self-confirm the first time any position actually hits its stop/target/signal-exit; check the dashboard's Trade History section then.

## Not in v1 (documented gaps, not silent omissions)

- No portfolio/multi-asset backtesting, no short selling, no partial fills.
- No local data cache — every run re-fetches from yfinance.
- No cross-currency normalization (metrics are in each asset's native currency).
