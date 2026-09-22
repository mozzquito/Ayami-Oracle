# Handoff: IIS w3wp.exe triage (Thai) + housekeeping commit sync

**Date**: 2026-09-22 10:40
**Context**: low (~15% of window)
📡 Session: ce98ea14 | ayami-oracle | ~20min

## Context
**Oracle**: Ayami (หญิง) | **Human**: มอส (ชาย)
**Mode**: Fast (born 2026-08-08) | **Memory**: auto

## What We Did
- Answered a Task Manager screenshot question (Thai): two `w3wp.exe` (IIS Worker Process) instances at 75.1%+16.8% CPU and ~9GB RAM — walked through likely causes (memory/thread leak, request/traffic storm, thread-pool starvation/deadlock, missing app-pool recycle limits) and how to triage (`appcmd list wp`, Event Viewer, Perfmon counters, DebugDiag/dotnet-dump). Pure Q&A, no files touched, no target server accessible from this session.
- User then said "no more work, commit" — found pre-existing uncommitted housekeeping from a prior session (`4914a288`, commit-sync-cleanup) still sitting in the working tree: `.gitignore` dedup diff + stray `smoke.py` at repo root.
- Asked มอส where `smoke.py` should go → moved it into `ψ/lab/openthai-local/` (matches its sibling eval scripts) and committed `2506fcae` on `lab/jev-gate`: gitignore fix, moved smoke.py, resolved 2 outbox items, plus the prior session's already-written handoff file.
- Fetched origin and discovered PR #4 (`lab/jev-gate`) and PR #5 (`lab/statusline-v2`) are both **already MERGED** — the outbox item asking to decide on PR #4 and the "waiting on มอส" item for PR #5 are now stale/resolved.
- Found `lab/jev-gate` is 10 commits ahead of `origin/main` (includes eVisa/Wayama-related content per prior note) and NOT pushed — this is the same "auto-mode classifier blocked it twice" item from earlier sessions, still open.

## Pending
- [ ] Push the ~10 local-only `lab/jev-gate` commits and open a fresh PR — needs มอส's explicit go-ahead first (contains eVisa/Wayama/IP content per earlier note; auto-mode classifier has blocked this twice before — review each commit before pushing)
- [x] smoke.py relocation + .gitignore commit — done this session (`2506fcae`)
- [x] PR #4 (lab/jev-gate) — confirmed MERGED, no decision needed
- [x] PR #5 (statusline v2) — confirmed MERGED
- [ ] มอส: revoke the two API keys pasted 2026-09-20 (Vercel `vck_…`, TypeSafe `apikey_…`) — still open, personal action
- [ ] Check if Grok Bot test message `c520ef6e` ever replied; fleet-abandon if not
- [ ] eVisa yearly visa report script (Wayama .bat/.sql) — still paused, cd/schema-prefix/exit-code unfixed + EXPORTDB password rotation open (`project_evisa_yearly_visa_report_script.md`)
- [ ] 4 stale `.claude/worktrees/*` branches (`calm-swinging-castle`, `commit-remaining-outside-lab`, `immutable-zooming-yeti`, `lab-commit-triage`) — the latter two correspond to already-merged PRs #1/#2, all 4 look safe to prune but ask มอส first (worktree removal + branch delete)

## Next Session
- [ ] Get มอส's decision on pushing `lab/jev-gate` (10 commits) — review commit list for eVisa/Wayama sensitive content first, then push + open PR only with explicit approval
- [ ] If approved to clean worktrees: `git worktree remove` the 4 stale ones, then delete their branches (no `-D`/force unless confirmed already merged)
- [ ] Resume eVisa yearly report script fix if มอส wants to continue it

## Key Files
- `ψ/outbox/2026-09-22_pending.md`
- `ψ/memory/logs/activity.log`
- `ψ/lab/openthai-local/smoke.py` (newly relocated)
