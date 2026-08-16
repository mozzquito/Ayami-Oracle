---
pattern: "Before kicking off a long batch job (hours of compute), check memory for documented failure patterns tied to the same tool/parameters and apply the fix proactively — not after the run completes with bad output"
date: 2026-08-13
source: "rrr: ayami-oracle"
concepts: [whisper, transcription, batch-jobs, proactive-fixes, background-monitoring]
---

# Apply a known fix before a long batch job starts, not after

## What happened

Kicked off a 5-file `mlx_whisper` transcription batch (~4 hours of audio total) with default
parameters. Within about a minute — before meaningful compute had been spent — stopped to check
whether this exact failure mode (hallucination loops) had a documented cause. It did:
`condition_on_previous_text=True` was already identified in an earlier session's retro as a
likely trigger. Killed the running job and restarted with `--condition-on-previous-text False`
before losing real time. The fix worked — isolated glitch lines (4-9 per file) instead of the
pervasive garbling seen in two previously-generated transcripts reused earlier in the same
session.

Separately, in the same session: a `Bash run_in_background` wait loop (`until grep -q
"ALL_DONE" ...`) got killed by the environment three times in a row, at shrinking intervals
(~55min, ~37min, ~11min), while the actual transcription process it was watching kept running
unaffected the whole time. Re-armed the identical wait loop after each of the first two kills
before finally switching to reactive status checks (only checking when the user asked) after
the third.

## Why

Long-running jobs are expensive to get wrong — the cost of a bad parameter compounds with
runtime. A 1-minute pause to ask "has this exact problem happened before, and is there a
documented fix?" before committing hours of compute is nearly free compared to discovering the
same problem after the fact. The background-wait failures are a different lesson: two failures
with the same shape (killed early, work unaffected) is enough signal that the *monitoring
mechanism* itself is unreliable in this environment — retrying it a third time added no new
information, just repeated the same negative result.

## How to apply

- Before starting any job you expect to run more than a few minutes unattended, check
  `ψ/memory/learnings/` (or equivalent memory) for prior failures involving the same tool. If
  one exists with a known fix, apply it before the first real run, not after reviewing bad
  output.
- If a background monitor/wait mechanism fails twice with a similar shape, stop re-arming it
  and switch strategy (e.g., reactive checks on user prompt) — don't wait for a third failure
  to confirm what two already showed. This is distinct from the underlying job failing — verify
  with `ps aux` or equivalent that the actual work is unaffected before concluding the monitor
  itself is the flaky part, not the work.
- Content reused from a prior session ("use the existing output, don't redo it") still needs a
  quality check before being handed off — permission to skip redoing work is not the same as a
  guarantee the existing output is good enough.
