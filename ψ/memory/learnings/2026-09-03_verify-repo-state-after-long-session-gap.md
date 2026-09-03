---
pattern: "When a session resumes after a long wall-clock gap, verify current repo state (git log/status) before assuming 'this session' and 'current project state' are the same thing"
date: 2026-09-03
source: "rrr: ayami-oracle"
concepts: ["session-resume", "long-lived-session", "verification"]
---

# Verify repo state after a long session-resume gap

A Claude Code session (`e0e471fd`) resumed 26 days after its last real activity. The session ID and scratchpad path were unchanged and still valid, but in the interim the repo had accumulated substantial unrelated work from other sessions — new `ψ/lab/` projects, weeks of retrospectives, unrelated commits. A stale background-task notification (a `maw serve` process from the old session) also resurfaced with no completion record.

**Rule**: a long-lived session ID spanning weeks of wall-clock time is not evidence that "this conversation" and "current project state" are still the same story. Before continuing stale in-conversation context (e.g. an instruction like "continue from where you left off" carried over from a much older turn), check `git log`/`git status` to see what's actually landed since — otherwise you risk writing a retrospective, status summary, or plan that silently treats someone else's work (or a stale instruction) as continuous with the current thread.

Corollary: a stopped/orphaned background task notification on resume (no completion record) is informational only — report it, don't assume it needs immediate remediation unless the human says the service is still needed.
