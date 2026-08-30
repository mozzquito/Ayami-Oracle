---
pattern: For any project directory that represents real, ongoing, multi-session work (especially one deployed to production), explicitly verify it's actually git-tracked early — don't infer safety from the parent repo existing.
date: 2026-08-17
source: "rrr: ayami-oracle"
concepts: [git-hygiene, verification, production-safety]
---

# Verify git-tracking for long-running project directories

While writing this session's retro, the routine `git status` step revealed that
`ψ/lab/market-backtester/` — a Python paper-trading system built and iterated over multiple sessions
across nearly a week, deployed live to Railway, with its own README documenting "pushed N commits" —
has never actually been `git add`ed in the `ayami-oracle` repo. It shows as untracked (`??`), not
gitignored (the directory's own `.gitignore` only excludes `.venv/`, `__pycache__/`, `.state/`, log
files — the source code itself was never staged).

**Why this went unnoticed**: across many sessions, work on this directory was described in terms that
implied durability — "committed," "shipped," "in the repo" — without ever running `git status` or
`git log -- <path>` specifically on it. The parent repo (`ayami-oracle`) *is* a real, active git repo
with real commits, which made it easy to implicitly assume anything worked on inside it was covered by
that same safety net. It wasn't — git tracking is per-path, not inherited from "being inside a repo
directory on disk."

**Generalizable rule**: the first time you do substantive work in *any* subdirectory of a repo — before
treating subsequent edits there as safely version-controlled — run `git status <path>` or
`git log --oneline -- <path>` once to confirm it's actually tracked. This is cheap (one command) and
the failure mode it catches (days/weeks of real work with zero git history, recoverable only from
wherever it happens to be deployed) is expensive and easy to discover far too late, as happened here.

**Escalation note**: this specific case (`ψ/lab/market-backtester/` untracked) was surfaced to Boss in
the session's retrospective but *not* resolved unilaterally — whether/when to commit it is Boss's call
(Principle 3, External Brain not Command), not something to `git add` and commit without asking first
given the directory also contains a `.venv/` and other local-only artifacts that need the right
`.gitignore` scoping verified before a first commit.
