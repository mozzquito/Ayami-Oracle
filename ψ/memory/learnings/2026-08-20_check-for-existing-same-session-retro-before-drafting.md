---
pattern: Before drafting a /rrr retrospective, check whether the current session already has one from earlier in the same session
date: 2026-08-20
source: rrr: ayami-oracle
concepts: [rrr, retrospective, duplication, session-management]
---

# Check for an existing same-session retro before drafting a new one

`/rrr` was invoked twice in one long session (`d4af5be6`): once mid-session at 07:40, covering a
`travelDocumentIssuedDate`/incident-investigation thread, and again later at 08:33 after the
active conversation context had compacted past an earlier, unrelated stretch of the same session
(query documentation + a production Oracle archiver incident). On the second invocation, a full
retrospective and lesson-learned file were drafted covering the *entire* session — including the
FONSECA/timestamp thread already retro'd at 07:40 — before it occurred to me to check whether this
session already had a retro. It did. The duplicate was caught only via `ls` on the day's
retrospective folder and the tail of `session-metrics.md`, partway through finishing the draft,
not before starting it.

**Rule**: before drafting any `/rrr` output, run the existing-retro check as step zero:
`ls` the current day's retrospective folder and check the last few rows of `session-metrics.md`
for the current session ID. If a retro already exists for this session, scope the new one to only
the genuinely new ground since that retro (and cross-reference the existing file by name instead
of re-narrating covered material), rather than writing a fresh end-to-end retrospective that
happens to overlap. A session that spans a `/rrr` invocation partway through is not a signal to
re-cover the whole session on the next call — it's a signal to scope tightly to what's new.

This is the concrete mechanism for a pattern already named abstractly in this skill's own
instructions (`.claude/skills/rrr/SKILL.md`'s `/rrr --quick` history references "caught the
repeat-retro pattern on 3rd tiny /rrr call, asked instead of duplicating again") — the check
needs to happen *before* drafting, not as a mid-draft realization.
