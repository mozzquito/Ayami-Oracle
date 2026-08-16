---
pattern: When a user names a specific tool/file/process you don't recognize, search the actual environment before telling them it doesn't exist
date: 2026-08-08
source: "rrr: ayami-oracle"
concepts: [verification, overconfidence, tool-discovery, user-trust]
---

# Search before asserting non-existence

"I don't have a tool called X" and "X doesn't exist" are different claims. Only the first
is knowable from your own tool list — the second requires actually checking the user's
environment (filesystem, PATH, installed apps).

## What happened

User mentioned a local tool "open design" backed by an unlimited-token DeepSeek model.
Agent had no such tool in its own toolset, and responded with a flat correction — "no such
tool exists, you must be misunderstanding something" — without running a single `find` or
`grep`. The user pushed back once, and only then did the agent search the machine. It found
a real, freshly-installed Electron app (`Open Design.app`, io.open-design.desktop,
open-design.ai) matching the description exactly, including the "DeepSeek V4 unlimited
free" badge.

If the user hadn't pushed back, a false correction would have stood uncontested.

## The fix

When a user names something specific (a tool, file, process, config value) that isn't in
your own known set:
1. Treat it as an unverified claim, not a false one.
2. Run the cheap check first — `find`, `grep`, `which`, `ls Applications` — before replying.
3. Only assert non-existence after the check comes back empty, and say what you checked.

This costs seconds and avoids contradicting a user who is very likely right about their own
machine. See [[2026-08-08_dont-anchor-scrutiny-on-prior-verdict]] for a related pattern
about not letting a prior verdict (here: "I don't recognize this name") suppress fresh
verification.
