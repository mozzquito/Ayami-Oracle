---
pattern: "Before invoking a sibling CLI agent (zcode/agy) in a mode that has failed before, check ψ/memory/learnings/ for that agent's documented quirks first and apply the known fix on the first attempt — don't rediscover an already-documented bug the hard way."
date: 2026-08-23
source: "rrr: ayami-oracle — self-hosted AutoClaw-replacement design session (2026-08-22)"
concepts: ["zcode", "agy", "background-bash", "memory-discipline", "self-referential-learning"]
---

# Check memory for known agent quirks before delegating, not after failing

While consulting zcode and agy in parallel for a design gap-check, zcode's background-mode
invocation failed immediately (exit 127) — the exact shell-alias-in-background failure already
documented in `ψ/memory/learnings/2026-08-18_zcode-alias-fails-in-background-bash.md`
(`zcode` is a `.zshrc` alias, not a real `PATH` binary, so `run_in_background: true` Bash calls
don't source the alias). The fix (call `node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs`
directly) was already written down from a prior session, but wasn't consulted before the first
attempt this session — the bug had to be hit again before the fix was applied.

**Why**: The whole point of writing a lesson to `ψ/memory/learnings/` is so a *future* session
doesn't pay the same cost twice. That value is only realized if the lesson is actually consulted
*before* the action it warns about, not recalled after the fact once the symptom reappears. In
this case the cost was small (one failed background call, quickly retried), but the pattern — a
documented fix sitting unused until the bug recurs — is exactly the kind of drift that erodes the
value of the whole learnings archive over time.

**How to apply**: Before shelling out to zcode or agy (or any sibling CLI agent) in a mode that
hasn't been used yet in the current session — especially `run_in_background: true`, a new flag
combination, or a first-time invocation — do a quick mental (or literal grep) check against
`ψ/memory/learnings/` for that agent's name. If a quirk is already documented, apply its fix
proactively rather than treating the first failure as new information.
