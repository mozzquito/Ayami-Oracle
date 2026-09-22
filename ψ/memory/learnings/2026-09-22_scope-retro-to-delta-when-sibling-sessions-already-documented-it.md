---
pattern: "When multiple concurrent worktree sessions race on the same wrap-up instruction, check git log for very recent commits on the same task before drafting a retro, and scope any new retro to the genuinely-unique delta rather than re-narrating what a sibling session already wrote."
date: 2026-09-22
source: "rrr: ayami-oracle — final commit-sync close-out (session 4914a288, following 3 sibling-session retros within ~20 minutes)"
concepts: ["rrr", "concurrent-sessions", "worktree", "memory-discipline", "check-for-existing-retro"]
---

# Scope a retro to the delta when sibling sessions already documented the same event

Four concurrent Claude Code worktree sessions on `ayami-oracle` (`4914a288`, `c2c57834`, `ce98ea14`,
`97c39087`) were each independently given the same "commit /forward /rrr" instruction within about
20 minutes of each other. Each discovered mid-flight that another session had already committed the
pending work, and three of them wrote full retrospectives documenting essentially the same event
(`10.26_commit-sync-forward-rrr.md`, `10.29_iis-triage-and-commit-sync.md`,
`10.29_cctv-rtsp-then-forward-rrr-wrapup.md`). By the time a fourth close-out request landed in
session `4914a288`, the only genuinely new content was three small commits cleaning up residue the
sibling sessions had left uncommitted.

**Why**: The existing lesson `2026-08-20_check-for-existing-same-session-retro-before-drafting.md`
covers the single-session case (don't re-retro the same session twice). This is the same failure
shape one level up: concurrent *sessions* on a shared repo can each independently satisfy "check for
an existing retro" and still all draft one, because each only checks its own session's history, not
siblings' commits. A repo with active parallel worktrees needs the check to be "did *any* recent
commit already cover this," not "did *this session* already write a retro."

**How to apply**: Before drafting a retro, check `git log --oneline -10` for commits from the last
~30 minutes that already describe the task at hand, and check `ψ/memory/retrospectives/<today>/` for
files with very recent mtimes regardless of which session ID they were written under. If a sibling
session already documented the substance, scope the new retro (if one is warranted at all) to only
the delta — the commits/actions that are actually new — and cross-reference the existing retro rather
than re-narrating it. This matters most right after a wrap-up instruction ("commit /forward /rrr")
that's generic enough for multiple sessions to receive and act on independently.
