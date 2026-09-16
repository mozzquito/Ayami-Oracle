# Crypto Paper Trading (Binance public REST only)

> **Provenance**: written by **Grok Bot** (a separate AI coding agent, xAI-backed, running
> on its own sandbox) on 2026-09-16, at มอส's request — an independent second implementation
> of the same general idea as the sibling `market-backtester` project, for comparison, not a
> port of its code. Ayami (Claude) reviewed every file, ran the test suite, and did a live
> dry run against real Binance data before bringing it into this repo and deploying it to
> Railway; Ayami did not write the implementation. See `ψ/memory/retrospectives/` around
> 2026-09-16 for the full back-and-forth (plan review, a real scheduling-time bug caught and
> fixed before building, universe corrected to match `market-backtester`'s own post-research
> watchlist).

**100% simulated.** No exchange API keys, no signed endpoints, no real orders.
Fetches public daily klines from Binance REST and evaluates two long-only strategies
on **closed daily bars only**.

## Quick start

```bash
cd crypto-paper-trading
python -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt
cp .env.example .env   # optional; defaults work
python main.py
```

One-shot daily evaluation, then exit. Artifacts land under `DATA_DIR` (default `./data`):

| File | Purpose |
|------|---------|
| `state.json` | Open positions, `last_evaluated_bar_date`, cash/equity summaries |
| `trades.csv` | Every fill attempt including `blocked_by_cap` |
| `equity.csv` | Daily equity snapshot |
| `run.log` | Human-readable run log |

## Closed-bar rule (critical)

1. Fetch `1d` klines.
2. If the **latest** bar is still forming (`close_time` in the future **or** `open_time` date is **today UTC**), evaluate on **index `-2` only**.
3. Never use today's incomplete candle for signals or fills.
4. **Idempotent:** if `state.json` already has `last_evaluated_bar_date` equal to that closed bar's UTC date, the run logs and exits `0` without re-trading.

Entries and exits are paper-filled at that closed bar's **close**. Stop-loss / take-profit are checked against that same daily close vs entry price (simple close-based stops — not intrabar highs/lows).

## Schedule tip

Run once per day after the UTC daily candle closes, e.g. **07:00–08:00 Asia/Bangkok** (= **00:00–01:00 UTC**). That gives Binance time to finalize the prior UTC day.

### Railway cron suggestion

```
# Cron (UTC): shortly after midnight UTC
0 0 * * *
# Command
DATA_DIR=/data python main.py
```

No secrets / API keys required in the environment.

## Universe (Binance USDT)

`BTCUSDT`, `ETHUSDT`, `SOLUSDT`, `TRXUSDT`, `BNBUSDT`, `NEARUSDT`, `POLUSDT`, `SHIBUSDT`

`POLUSDT` is Polygon post-rebrand (not `MATICUSDT`). Override with env `SYMBOLS`.

## Strategies

### 1. `book_rsi_ma_mtf`

- **RSI(14)** (Wilder / EWM).
- **Long** when RSI crosses **up** through oversold (default 30): previous RSI &lt; 30 and current RSI ≥ 30.
- **Trend gate:** closed bar close must be **above** SMA(`TREND_MA_PERIOD`, default 50) of daily closes.
- **Exit:** 5% stop-loss, 10% take-profit, or RSI crosses back **below** 30 (reversal).

### 2. `rsrs_trend`

- **RSRS** = OLS linear-regression **slope** of close vs time index `0..N-1` over window `RSRS_WINDOW` (default **18**).
- **Long** when RSRS crosses **above** `RSRS_THRESHOLD` (default **0.0** — configurable; 0 means slope turns non-negative).
- **Exit:** 2.5% SL, 5% TP, or RSRS crosses back **below** threshold.

## Sizing & risk

| Rule | Default |
|------|---------|
| Slot size per symbol×strategy | `SLOT_USD=10` |
| Max concurrent opens (whole book) | `MAX_OPEN=5` |
| Start | Empty book |
| Notional | Each new long spends $10 at close (`qty = 10 / price`) |

When more entry signals fire than free slots, fills are deterministic:

1. Symbol list order (config / default universe order)
2. Then strategy order: `book_rsi_ma_mtf` before `rsrs_trend`

Excess signals are **not** dropped silently — a `trades.csv` row is written with `reason=blocked_by_cap`.

## Environment variables

See `.env.example`. Summary:

| Variable | Default | Meaning |
|----------|---------|---------|
| `DATA_DIR` | `./data` | State / CSV / log directory |
| `SLOT_USD` | `10` | Notional per open |
| `MAX_OPEN` | `5` | Cap on concurrent positions |
| `RSI_PERIOD` | `14` | RSI lookback |
| `RSI_OVERSOLD` | `30` | Cross-up / reversal level |
| `TREND_MA_PERIOD` | `50` | SMA trend gate |
| `RSRS_WINDOW` | `18` | OLS slope window |
| `RSRS_THRESHOLD` | `0.0` | RSRS cross level |
| `BINANCE_BASE_URL` | `https://data-api.binance.vision` | Public REST base |
| `KLINES_LIMIT` | `200` | Daily bars to fetch |
| `SYMBOLS` | (universe above) | Optional comma-separated override |

## Tests

```bash
pip install pytest
pytest -q
```


## Network note

Default `BINANCE_BASE_URL` is `https://data-api.binance.vision` (public market-data host). The client also falls back to `https://api.binance.com`. Some regions get HTTP 451 from `api.binance.com`; use the data-api host. No API keys are used.
## Disclaimer

Educational paper trading only. Past simulated performance is not indicative of future results. Do not connect API keys or place live orders with this code.
