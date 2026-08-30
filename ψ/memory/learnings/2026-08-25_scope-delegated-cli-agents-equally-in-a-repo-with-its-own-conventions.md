---
pattern: When delegating to autonomous CLI coding agents (zcode/agy) running inside a repo with its own CLAUDE.md conventions, restrict them equally (--sandbox / --disallowedTools) from the first call — don't protect one and leave the other exposed
date: 2026-08-25
source: rrr: ayami-oracle
concepts: [zcode, agy, delegation, permissions, session-activity-hook, multi-agent]
---

# Scope delegated CLI agents equally in a repo with its own conventions

## What happened

Delegated a pure-brainstorming task to both `/zcode` and `/agy` in parallel. `zcode` was launched
with `--disallowedTools "Edit Write Bash(git*)"` to keep it read-only. `agy` was launched with only
`--mode plan` and no explicit write-blocking. `agy` failed immediately (exit code 1) — it tried to
run the repo's own required "Session Activity" logging convention (writing
`ψ/inbox/focus-agent-*.md` and appending to `ψ/memory/logs/activity.log`, per this project's
CLAUDE.md), and the Bash permission check for that write was denied in non-interactive background
mode with nobody able to answer the prompt.

This is not a one-off — `agy`'s own skill doc (`.claude/skills/agy/SKILL.md`) already documents
this exact failure mode from a prior session ("agy's Session Activity hook block — which broke the
exact same consult in a prior session"), and this session's own `session-metrics.md` history shows
it recurring across multiple earlier sessions too. The pattern was known before this session started.

## The rule

When an autonomous coding agent (zcode, agy, or similar) is pointed at a repo (`--cwd`) that has
its own CLAUDE.md with mandatory conventions (session-activity logging, focus files, etc.), assume
it will try to follow those conventions like any other agent working in that repo — because it
reads the same CLAUDE.md. For a task that is pure analysis/brainstorming and genuinely needs no
file writes, scope it down defensively from the very first call:

- `agy`: add `--sandbox` (or `--mode plan` alone is not sufficient — it still permits Bash writes)
- `zcode`: add `--disallowedTools` covering `Edit Write Bash(git*)` at minimum, and consider
  blocking the specific session-activity file paths if the repo enforces them via Bash rather than
  Edit/Write

Apply the same restriction level to every agent in a parallel delegation — don't harden one and
leave a sibling call exposed to the same repo's conventions. If one agent needs the restriction,
the other one launched into the same `--cwd` needs it too.

## Why this matters

The cost isn't just the failed call — it's the wasted round-trip to diagnose (the failure is
silent unless you `cat` the output file) and re-run, and it recurs every time this detail is
forgotten, because the underlying cause (the repo's own CLAUDE.md instructing every agent that
reads it to log activity) doesn't go away between sessions.
