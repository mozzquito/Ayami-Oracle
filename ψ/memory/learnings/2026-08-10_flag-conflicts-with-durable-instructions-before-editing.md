---
pattern: When a new user instruction textually conflicts with an existing durable instruction (global CLAUDE.md, project config), surface the conflict and ask before editing — don't silently resolve it in either direction
date: 2026-08-10
source: rrr: ayami-oracle
concepts: [durable-instructions, conflict-detection, ask-vs-guess, global-config]
---

# Flag conflicts with durable instructions before editing

Moss asked to add a rule ("every SDLC stage must have zcode/agy help") to `~/.claude/CLAUDE.md`.
The file already contained an explicit statement that directly conflicted with the literal
reading of the new request: "the user does not want a separate person, bot, or external tool
doing this." A silent edit in either direction — ignore the new request to protect the old rule,
or overwrite the old rule to satisfy the new request — would have baked an unverified guess into
a file that shapes every future session across every project.

Instead: named the conflict explicitly, then used AskUserQuestion with concrete options
(consult-only / delegate-work / skill-specific-only) and a recommended default. The user's
answer matched the recommended default — but that's not evidence the question was unnecessary;
it's evidence the check was cheap insurance against a low-probability, high-cost wrong guess.

**Why**: Global/durable instruction files (`~/.claude/CLAUDE.md`, project `CLAUDE.md`, skill
configs) are read by every future session. A wrong silent edit there isn't a one-off mistake —
it's a standing wrong instruction that compounds across sessions until someone notices and
corrects it. This is categorically different from a one-off code change, where being wrong costs
one review cycle.

**How to apply**: Before editing any durable/global instruction file, re-read the existing text
for statements that a literal reading of the new request would contradict. If found, don't
pattern-match to "the user obviously means X" and proceed — ask, even under an "auto mode, bias
toward action" directive. The bias-toward-action default is for reversible, low-blast-radius
actions; edits to files that steer all future sessions are the opposite of that, closer to the
"decision only the user can make" carve-out that auto-mode instructions themselves reserve for
stopping and asking.
