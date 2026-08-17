"""Shared constants for the backtester. Single home for magic numbers."""

DEFAULT_COMMISSION_PCT = 0.001   # 0.1% per trade (round-turn charged on both entry and exit)
DEFAULT_SLIPPAGE_PCT = 0.0       # off by default; user opts in via --slippage
DEFAULT_SIZE_PCT = 1.0           # 100% of available cash per entry ("fixed" sizing mode)
DEFAULT_CAPITAL = 100_000.0
RISK_FREE_RATE_ANNUAL = 0.0      # kept simple for v1; Sharpe uses excess-return = 0 baseline

# Position sizing per Ch. 12 ("Risk Management Essentials") of Deep Learning for Finance.
DEFAULT_SIZING_MODE = "fixed"    # "fixed" | "fractional" | "kelly"
DEFAULT_RISK_PCT = 0.01          # "fractional" mode: risk 1% of account per trade (book's stated practical default)
DEFAULT_KELLY_PRIOR_WIN_PROB = 0.5   # "kelly" mode: assumed win probability before enough trade history exists
DEFAULT_KELLY_PRIOR_PAYOFF = 1.5     # "kelly" mode: assumed avg-win/avg-loss ratio before enough trade history exists
MIN_TRADES_FOR_KELLY = 10        # below this many closed trades, kelly mode falls back to the priors above
KELLY_MIN_FRACTION = 0.02        # floor so a negative-edge estimate can't permanently zero out sizing —
                                  # f=0 means "never trade again," which would freeze the stats that could
                                  # let the estimate recover. A small probe size keeps the loop alive.

# Trading-day counts used to annualize Sharpe/CAGR — differs by market because
# crypto trades every calendar day while equities/forex only trade weekdays.
ANNUALIZATION_DAYS = {
    "us": 252,
    "set": 252,
    "forex": 260,
    "crypto": 365,
}

# Ticker suffix/format rules applied when the user passes a bare symbol.
# A symbol that already contains the market's marker (e.g. "PTT.BK") is left as-is.
MARKET_SUFFIX = {
    "us": "",
    "set": ".BK",
    "crypto": "-USD",
    "forex": "=X",
}

VALID_MARKETS = tuple(MARKET_SUFFIX.keys())

# Correlation guard (added 2026-08-15, agy's suggestion): the 6 crypto symbols in
# cloud_run.py's watchlist tend to move together (>0.85 correlation in practice) — a
# broad crypto rally can fire 5+ entry signals simultaneously, which isn't really 5
# independent bets, it's one leveraged bet on "crypto goes up" wearing 5 costumes. Caps
# how many positions can be open at once per market, independent of how many symbols
# in that market currently show a bullish signal.
MAX_CONCURRENT_POSITIONS = {
    "crypto": 2,
    "forex": 2,
}

# Per-strategy stop/target overrides, keyed by market. Only strategies that have been
# explicitly backtest-tuned appear here — everything else falls back to whatever the
# caller passes via --stop-pct/--target-pct (or None).
#
# rsrs_trend (added 2026-08-17): this strategy trades far more often than book_rsi_ma_mtf
# (up to 366 trades/symbol on crypto vs ~90), so it's more sensitive to stop/target
# distance. Halving book_rsi_ma_mtf's distances improved both return AND drawdown
# together across the 9-symbol watchlist (2023-2026 backtest) rather than trading one
# off for the other — avg return +43.4%->+50.9%, avg max-drawdown -46.3%->-39.8%, worst
# single-symbol max-drawdown -81.1%->-65.8%. Not wired into cloud_run.py's production
# SYMBOLS yet (rsrs_trend itself isn't live there) — this is the reference default for
# whenever it is.
STRATEGY_STOP_TARGET_PCT = {
    "rsrs_trend": {
        "crypto": {"stop_pct": 0.025, "target_pct": 0.05},
        "forex": {"stop_pct": 0.015, "target_pct": 0.03},
    },
}
