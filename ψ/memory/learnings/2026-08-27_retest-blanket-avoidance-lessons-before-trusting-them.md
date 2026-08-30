---
pattern: "A prior learning that concludes 'stop using tool X entirely, workarounds don't help' should get one cheap targeted retry before being trusted as still valid, not indefinite deference — tool/environment behavior shifts between sessions, and the original diagnosis can turn out narrower than the blanket conclusion stated."
date: 2026-08-27
source: "rrr: ayami-oracle"
concepts: ["agy", "zcode", "sibling-agent-consult", "memory-hygiene", "sdlc-workflow"]
---

# Learned: re-test blanket "give up on tool X" lessons before trusting them

## What happened

`ψ/memory/learnings/2026-08-22_agy-blocked-by-activity-log-hook-dont-retry-identically.md`
concluded, after two failed attempts and one workaround attempt, that "agy `-p`/headless
mode is currently unusable for delegated review/analysis tasks in this repo/environment
... skip agy entirely after one failed attempt per session — do not try scoping/workaround
variants, they don't help."

On 2026-08-26, during `/learn github.com/Tencent/AI-Infra-Guard`, agy's first call hit the
exact same failure (denied Bash permission on the Session Activity logging preamble). Per
the old lesson, the "correct" move was to give up on agy for the session. Instead, a more
targeted variant was tried — an explicit "don't run any file-writing bash, just answer in
text" instruction embedded directly in the prompt (not a `--cwd`/`--add-dir` scoping trick,
which the old lesson had already tried and ruled out) — and it succeeded on the first retry.

## Why this matters

The old lesson's blanket conclusion doesn't survive a more targeted variant. That doesn't
mean the original diagnosis was wrong — the exact failure shape it documented (identical
retry, or `--add-dir` scoping) may still fail exactly as described. What changed is that a
*different* kind of workaround (steering the prompt itself away from the triggering
behavior, rather than scoping the working directory) wasn't tried in the original
investigation and turned out to work.

## What to do instead

- Before deferring to a memory that says "stop using X entirely, nothing helps," check
  whether the specific workarounds it already ruled out are the same ones you're about to
  reach for. If you have an untried angle (e.g. prompt-level instruction vs. CLI-flag
  scoping), it's worth one cheap attempt rather than automatic avoidance.
- When a targeted retry *does* succeed against a "permanently broken" lesson, update that
  lesson with the counter-example instead of leaving the stale blanket conclusion as the
  only guidance on file — otherwise the next session either repeats the failed workarounds
  the old lesson already ruled out, or gives up prematurely on an angle that actually works.
- This generalizes beyond agy: any "give up on tool Y" learning is a hypothesis pinned to
  the environment/tool version at the time it was written, not a permanent fact.

## Related

[[2026-08-22_agy-blocked-by-activity-log-hook-dont-retry-identically]] — the lesson this
one supersedes/qualifies. That file's "skip entirely" conclusion should be read alongside
this counter-example, not in isolation.
