---
name: match-agent-mode-to-task-execution-need
description: When delegating to a CLI coding agent (zcode/agy/grok) in a single non-interactive call, pick a mode that permits the actual execution the task requires — a read-only "plan" mode on an execution-shaped task just produces a plan and waits for approval that never comes
date: 2026-09-16
source: rrr: market-backtester overnight research (ayami-oracle)
concepts: [agent-delegation, agy, zcode, cli-tools, task-mode-selection]
---

# Match agent CLI mode to what the task actually needs to do

## What happened

Delegated a walk-forward validation task to agy twice, both times using `--mode plan`
(agy's "safe default for review/analysis"). Both times agy produced only an implementation
plan and explicitly asked to "review the plan... let me know if you'd like me to proceed" —
timing out at 5 minutes and then 15 minutes with zero actual results, because `--mode plan`
structurally cannot write or execute a script, and the task required running real backtests
to get real numbers. The same pattern happened again later in the same session with a
different research task before the lesson was internalized.

The fix: relaunch with `--mode accept-edits` (scoped to a scratch directory, not
production files) and an explicit instruction in the prompt: *"This is a non-interactive
single-shot call — there is no follow-up turn where I can say 'proceed.' Do NOT stop to
ask for plan approval; write the script and run it now, in this same call, and report the
actual numeric results."* Both retries then delivered genuinely careful, real, well-reasoned
results on the first attempt.

## Generalizable rule

Before delegating a task to a non-interactive CLI agent (zcode, agy, grok, or similar),
classify the task shape first:

- **Review/analyze/critique existing code, no changes needed** → a read-only mode
  (`--mode plan`, `--disallowedTools "Edit Write"`) is correct and safer.
- **Requires running code to produce a real result** (backtest, test suite, data
  analysis, build verification) → the agent needs write/execute permission for at least
  a scratch directory, even if the *goal* is just a report. A "plan-then-execute" agent
  pattern doesn't work in a single non-interactive call — there's no second turn for it
  to receive approval on the plan it drafted, so it will time out waiting.

When using an execution-capable mode, state directly in the prompt that this is a
one-shot call with no follow-up turn, and that the agent should skip any "let me know if
you'd like me to proceed" checkpoint and just do the work. This isn't about trusting the
agent with more permission than needed — scope the write access narrowly (a `/tmp/`
scratch directory, `--add-dir` limited to what's needed) rather than loosening the mode
globally.

## How to apply

Any time a delegation prompt contains verbs like "run," "backtest," "test," "measure," or
"report the actual numbers" — that's an execution-shaped task. Default to an
execution-capable mode from the first attempt, not as a fallback after a timeout.
