---
name: recheck-rejected-candidates-full-history-not-just-recent-window
description: When a symbol/strategy selection turns out to have been survivorship-biased, don't just fix the flagged picks — re-check every originally-rejected alternative against BOTH a recent out-of-sample window AND the full available history before adding any of them back, or you repeat the same bias in the opposite direction
date: 2026-09-16
source: rrr: market-backtester overnight research (ayami-oracle)
concepts: [walk-forward-validation, survivorship-bias, overfitting, backtesting, out-of-sample]
---

# Re-checking rejected candidates needs both a short window AND the full history

## What happened

A crypto watchlist's two worst-performing symbols (DOGE, AVAX) were confirmed to have been
originally selected on survivorship-biased backtest numbers — they were the best of a
10-candidate comparison, not an unbiased edge estimate. A walk-forward out-of-sample test
confirmed both went negative with a 0% win rate out-of-sample.

The natural next step was checking the originally-*rejected* candidates from that same
2026-09-01 selection to see if any deserved a second look. The first pass checked them only
against the same short out-of-sample window (2026-07-01 to 09-16) used to disqualify
DOGE/AVAX — and several (LTC, LINK, MATIC's own `rsrs_trend` variant) looked genuinely good
in that window. But a second check against each candidate's **full available multi-year
history** revealed all of them were actually net *negative* over the long run — the short
window had just caught a lucky recent bounce. Only one candidate (POL, on
`book_rsi_ma_mtf`) showed positive results on **both** checks, and that convergence — not
either check alone — was what made it trustworthy enough to add.

## Generalizable rule

A short out-of-sample window and a full-history backtest answer two different, both
necessary questions:

- **Full history**: does this candidate have any real edge at all, averaged over enough
  time to not be dominated by one lucky or unlucky stretch?
- **Recent out-of-sample window**: is that edge still showing up now, or has it decayed /
  was it never there to begin with (the exact failure mode being investigated)?

Checking only the second, after having just learned the first check matters, repeats the
same class of mistake in the opposite direction — cherry-picking a recent lucky window
instead of a cherry-picked historical maximum. Require **both** checks to agree before
promoting any previously-rejected candidate back into production, not just whichever
single check happens to be the one currently in focus.

## How to apply

Whenever re-evaluating candidates that were previously screened out (coins, strategies,
parameter sets, model variants), run the newest validation method being used to catch the
current problem AND the older method that was trusted before — a candidate only clears
the bar if it looks good under both, not just the one being freshly emphasized.
