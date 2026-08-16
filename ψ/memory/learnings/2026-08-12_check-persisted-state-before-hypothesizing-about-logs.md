---
pattern: "When live-running state seems broken, check what it actually persisted before hypothesizing about why the observation tool (logs) looks wrong"
date: 2026-08-12
source: "rrr: ayami-oracle (market-backtester Railway cron deploy)"
concepts: ["debugging", "cloud-deploy", "railway", "observability", "diagnostic-ordering"]
---

# Check persisted state before hypothesizing about missing logs

While debugging a Railway cron job whose piped command (`advise | notify`) showed no
stdout in `railway logs`, I reached for plausible fixes (`PYTHONUNBUFFERED=1`, PATH
theories) across several redeploy cycles before checking the one piece of evidence that
would have settled it immediately: the mounted volume's state-file mtime. That file
proved the pipeline had already executed correctly on the very first "silent" run — the
missing logs were a capture gap specific to shell pipelines, not a functional failure.

**Why**: A stateful system's own persisted output (a file mtime, a DB row, a written
artifact) is cheaper and more decisive evidence than reasoning about buffering/PATH/
environment differences. Logs are one observation channel among several; when a system
has any other durable side effect, check that side effect first — it directly answers
"did the code run and do the right thing," while log absence only tells you "the log
pipeline didn't capture something," which is a different and often unrelated question.

**How to apply**: Before adding "fix" env vars or changing invocation style to chase
missing/weird logs from a deployed job, first check whatever durable artifact the job
would have produced if it ran correctly (a written file, an updated timestamp, a state
row, a sent notification). If that artifact is correct, the code is fine — stop chasing
the logs and treat it as an observability quirk, not a bug. This generalizes beyond
Railway: any cron/batch job with a persisted side effect should be diagnosed
artifact-first, logs-second.

Related: [[2026-08-11_learned-deep-learning-for-finance-sofien]] (same session, the
market-backtester tool this deploy serves)
