---
pattern: "Before delegating to a sibling CLI agent (zcode/agy) that has a known environment quirk, grep ψ/memory/learnings/ for that agent's name first — repeating an already-documented failure wastes a round-trip a two-second check would avoid"
date: 2026-09-03
source: "rrr: ayami-oracle (fb-video-review-and-claude-tag-team-repo)"
concepts: ["agy", "zcode", "delegation", "memory-first", "headless-permissions"]
---

# Check memory for known agent quirks before repeating a documented failure

agy was delegated a task in headless/background mode twice in the same
session — first with a file-read prompt, then with the prompt content
inlined instead — and both attempts failed identically with
`"no output produced — a tool required the 'command' permission that
headless mode cannot prompt for."` This exact failure mode was already
documented in `ψ/memory/learnings/` from a prior session
(2026-08-30, agy headless permission double-block), but that memory was
not consulted before either attempt.

**Rule**: before delegating to a sibling CLI agent (agy, zcode, or any
future addition) — especially in headless/background/non-interactive
mode — grep `ψ/memory/learnings/` for that agent's name first. If a quirk
is already documented (alias-in-background failures, permission walls,
retry-blocking hooks, etc.), apply the known workaround or known
limitation immediately rather than rediscovering it through a failed
attempt. This generalizes to any external tool this Oracle delegates to
repeatedly: a memory check costs seconds; an uninformed repeat of a known
failure costs a full round-trip and, when the user is waiting on the
result, a decision point they shouldn't have had to make.

See [[fb-video-review-and-claude-tag-team-repo]] retrospective for the
concrete incident this was distilled from, and
[[oracle_agy_headless_permission_double_block]] (2026-08-30) for the
original documented quirk this repeated.
