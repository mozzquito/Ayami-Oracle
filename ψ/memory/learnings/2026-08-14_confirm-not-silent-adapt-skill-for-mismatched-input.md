---
pattern: "When a skill's literal instructions assume one input shape (e.g. /learn assuming a git repo) and actual input doesn't fit (a blog URL), say so in one sentence before silently substituting a lighter approach — and if a memory-save offer goes unanswered, follow up explicitly or default to saving rather than letting it evaporate"
date: 2026-08-14
source: "rrr: ayami-oracle"
concepts: ["rrr", "skill-adaptation", "memory-persistence", "agent-decision"]
---

# Confirm, don't silently adapt, when a skill's assumed input shape doesn't match

Two `/learn` invocations this session targeted blog articles, not GitHub repos. The `/learn`
skill is built entirely around `ghq get` + `origin/` symlink + 3 parallel Haiku agents exploring
a codebase — none of that applies to a blog post. Skipped the clone/multi-agent pipeline both
times and just WebFetched + summarized directly. The *substitution* was correct, but it was
never surfaced to the user as a substitution — it just silently happened.

Consequence: the first article's offered-but-unconfirmed "want this saved?" question was never
followed up on before moving to the next command, leaving that summary unpersisted anywhere
outside the chat transcript — for a fact the user was using to make a decision (monetization
angle). The second, near-identical command got explicitly saved because the user said so
directly that time. Same command, same session, inconsistent outcome, self-inflicted.

**Rule**: when adapting a skill because the input doesn't fit its literal assumptions, say one
sentence naming the adaptation. If a save/persist offer goes unanswered, either chase it down
before moving on, or default to saving (per "Nothing is Deleted") rather than let it silently
drop.
