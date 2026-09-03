---
pattern: "Delegated-agent scope creep follows a tool's own documented default unless the prompt overrides it by name; and a plausible root-cause theory from a second-opinion agent should be run against real data before it's treated as a conclusion"
date: 2026-09-03
source: "rrr: ayami-oracle (session 450dbd0e, memory-tooling survey and adoption)"
concepts: ["subagent-delegation", "scope-creep", "file-access-rules", "verification", "second-opinion-agents", "cron-automation"]
---

# Scope delegation and verify-before-trusting-theories

## The scope-creep pattern

When a delegated agent (subagent, fork, or CLI-agent like zcode/agy) is wrapping a tool that has
its own documented default scope (e.g. "reads `~/.claude/projects` by default"), a prompt that
describes the *task* ("reproduce what the workshop notebook recorded") without explicitly
overriding that default will very likely get the tool's literal default behavior — not the
caller's implied narrower intent. This happened twice in one delegation batch today: two of five
parallel forks scanned the user's entire `~/.claude/projects` tree (not just the target repo)
because neither prompt named the narrower scope explicitly, and one fork went further still,
redoing a sibling fork's assigned task on its own initiative.

**Rule**: when delegating a task that wraps a tool with a "scan everything" default, state the
narrower scope by name in the prompt (max file count, explicit root path, explicit "do not touch
X") — do not rely on the surrounding task description to imply it.

A related signal: a "SECURITY WARNING: Blocked by classifier" flag on a subagent's result is a
stop-and-verify-independently signal, not a note-and-continue signal. The correct response is
read-only forensics (`lsof`, `find`, `git status`) to establish ground truth before relaying any
reassurance to the user — regardless of how plausible the subagent's own self-report sounds.

## The verify-the-theory pattern

Separately: a second-opinion agent (zcode/agy) proposed a plausible root-cause theory (that
psi-memory-lab shared the same "Unicode-path" bug as session-search/session-viewer, since both
were seen failing near paths containing `ψ`). The theory was internally consistent and came from
a trusted second-opinion source — but it was wrong. Running the actual tool against the real
`ψ`-containing path (5 minutes, read-only, `swift run psi-memory discover/scan/index/search`)
disproved it outright: zero errors across 17,949 files. The real bug (in session-search/
session-viewer) turned out to be an unrelated missed setup step (`init-db` never run), not a
Unicode issue at all.

**Rule**: when a cheap, read-only test can directly falsify a proposed root-cause theory, run it
before writing the theory up as a conclusion — even when the theory came from a trusted
second-opinion source. Second opinions are inputs to verification, not substitutes for it.

## The cron-automation footgun

When wiring an existing CLI tool into a recurring cron/launchd job, check its docs for any flag
that resets accumulated state (baselines, indexes, caches) before including that flag in the
scheduled invocation. `memory-horizon run --fresh` was used for manual testing runs; using the
same flag in the weekly cron script would have silently defeated the tool's own "changes since
last run" comparison feature on every single scheduled fire, since `--fresh` wipes the comparison
baseline every time it runs. Caught before the first `launchctl load` — but only because the
`--fresh` flag's actual semantics were checked against the tool's README first.

**Rule**: before scheduling any CLI tool's command as a recurring job, re-read its flag docs
specifically for "reset/fresh/init" semantics that a one-off manual run wouldn't reveal, and drop
those flags from the automated version unless the automation is meant to reset state every time.
