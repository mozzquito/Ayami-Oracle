---
pattern: "Before writing a session retrospective, verify what happened in THIS session's own transcript, not what's sitting in repo-level state (git log/status) — repo state reflects every concurrent session's work, not this one's"
date: 2026-09-13
source: "rrr: ayami-oracle"
concepts: ["rrr", "retrospective", "session-scope", "multi-session", "verification"]
---

# Verify session scope before retro, not repo state

A `/rrr` request arrived on a transcript that had sat dormant for 28 days (last real
activity 2026-08-15 16:12, resumed 2026-09-13 14:34, closed one minute later). `git log`
and `git status` showed real, substantial work in the same repo during that gap — a
device-monitor POC commit, a new skill install, several already-written retrospectives
dated across the gap. The instinctive move was to write a retro summarizing that work
since it was right there in git history. That would have been fabrication: none of it
happened in *this* session's conversation — it happened in other Claude Code sessions
running concurrently/sequentially against the same repo, each of which already wrote its
own honest retrospective.

Caught it by mining this session's own `.jsonl` directly for every message type (not
just `user` text — `assistant`, `tool_use`, everything) between the last retro's
timestamp and now, and getting a flat zero. That's the actual, verifiable scope of the
session being retro'd.

**Generalizable rule**: a repo's git log/status is shared state across every session
that touches it — it is never evidence for what *this specific session* did. When
writing any session-scoped artifact (retrospective, handoff, summary), verify against
that session's own transcript/timestamps first. This matters most exactly when it's
tempting to skip the check — a long gap, a trivial-looking request, plausible-looking
material sitting right there in repo state. The check is cheap (one grep/python pass
over the session's own `.jsonl`); the cost of getting it wrong is a retrospective that
credits the wrong session, pollutes the pattern-detection value of `session-metrics.md`,
and misrepresents what actually happened when someone reads it back later.
