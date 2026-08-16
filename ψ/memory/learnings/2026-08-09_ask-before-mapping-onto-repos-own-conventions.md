---
pattern: When a request's wording overlaps a repo's own internal convention, don't assume that convention is what the user means — ask, especially when the two interpretations produce completely different artifacts
date: 2026-08-09
source: rrr: ayami-oracle
concepts: [scope-clarification, ambiguous-request, personal-vs-project, session-log-vs-diary]
---

# Ask before mapping a request onto the repo's own conventions

Boss asked Ayami to "keep a record of daily life" (เก็บประวัติชีวิตประจำวัน). The repo's own CLAUDE.md defines a "Session Activity" convention using nearly the same words (focus files, activity.log, working/completed states) for tracking *dev-task* state. Ayami pattern-matched the request onto that existing convention and built a technical work-session log — without asking whether Boss meant his own real life instead. He did: meetings, food, conversations, not git commits and shell commands. The wrong file had to be built, explained, and left in place (per Nothing-is-Deleted) before the right one could start.

**The generalizable trap**: a repo having its own internal terminology or convention for a phrase does not mean every user request using similar words refers to that convention. This is easy to miss specifically *because* the codebase's own language primes the interpretation — the more natural the internal-convention reading feels, the more important it is to check it's not crowding out the plain-English reading the user actually intended.

**Rule**: when a request could plausibly mean "the project's own internal pattern for this term" OR "something about the user's life/work/world outside the codebase," ask a one-line clarifying question before building anything. This costs one turn. Guessing wrong costs a full build-explain-rebuild cycle, and in the case of a personal diary, wastes a slot in an append-only file (can't just delete the mistake).

**Signal to catch it before it happens**: if the interpretation you're about to act on requires zero new information from the user — everything needed is already sitting in the repo (git log, existing docs, existing conventions) — that's a mild warning sign, since the very-online interpretations of a request also tend to be the low-effort ones. Genuinely personal, real-world requests (food, meetings, feelings, conversations) usually can't be fully assembled from repo state alone; a request that *can* be fully answered from repo state alone is worth a beat of suspicion — is that actually what was asked, or just what was easiest to build from what's already at hand?
