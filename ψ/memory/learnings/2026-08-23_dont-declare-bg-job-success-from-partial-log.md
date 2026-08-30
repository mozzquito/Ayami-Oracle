---
pattern: "Before declaring a long-running background/scheduled job successful, either wait for its actual completion signal (exit code, final output line) or explicitly label the claim as 'started successfully, completion unverified.' A healthy-looking first few seconds of log output from a multi-minute job proves nothing about whether it will finish."
date: 2026-08-23
source: "rrr: ayami-oracle — grafana-report-bot launchd deploy"
concepts: ["verification", "background-jobs", "launchd", "cron", "self-evaluation-loop"]
---

# Learned: a job's first 15 seconds of log output is not evidence it will complete

## What happened

While deploying `grafana-report-bot`'s launchd scheduling, I triggered a manual test
(`launchctl start com.ayami.grafana-report.daily`) to confirm the launchd-invoked path
worked (different PATH/env than a direct interactive run). I checked the log after 15
seconds, saw `"Launching headless Chromium… / Logging into…"`, and reported to the
user that the launchd path was verified working — without waiting for the ~12-minute
full run to actually finish or checking its exit status.

Hours later, when the user asked "เหลืออะไรบ้าง" (what's left), I actually checked the
log in full and `launchctl list`'s exit-status column, and found: the same manual test
run had in fact failed (`Grafana login timeout` — a VPN blip after the initial
connection succeeded), and separately the real scheduled 16:00 run had also failed
(Mac battery-sleep killed it mid-run, root-caused later to a 1-minute idle-sleep
timeout on battery power). I had to walk back an earlier "deployed and verified"
claim.

## The mistake

Treating "the first visible log lines look healthy" as equivalent to "the job
succeeded." A process can get past its first network call and still fail minutes
later from a completely different cause (session/VPN drop, resource exhaustion,
OS-level sleep, a downstream step's bug). The only real evidence of success is either
the job's own completion signal (final log line, written output file, `$?`/exit code)
or an explicit, honest "still running, not yet confirmed" caveat.

## How to apply

For any job expected to run more than ~30 seconds:
- If checking on it mid-run, say so explicitly ("still in progress, not yet
  confirmed complete") rather than extrapolating success from partial output.
- Schedule a follow-up check (wakeup, notification, or explicit "come back later")
  timed to the job's *actual* expected duration, not a token glance.
- When later reporting status, check the actual completion artifact (exit code, log's
  final line, output file's existence/timestamp) — not memory of what you saw
  partway through.
- This is the same discipline as [[feedback_verify_before_asserting]] applied
  specifically to time-extended background work, where the temptation to
  extrapolate from an early "looks fine" signal is strongest.

## Related

This exact session caught and self-corrected the same category of error twice: once
by making the mistake (12:41 premature "verified" claim) and once by catching it
(21:47, when asked a status question, actually checking logs instead of repeating the
earlier claim). See the session's own retrospective self-audit for the recurring
pattern note — this shape of error ("declared success/completion before full
verification") has now recurred across multiple sessions per
`ψ/memory/learnings/session-metrics.md`, which per parent CLAUDE.md's
"Self-Evaluation Loop" means it's due for a standing-check conversation with มอส
rather than another one-off correction.
