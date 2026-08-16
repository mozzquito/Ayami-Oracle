---
pattern: Verify a delegated coding agent's diff/typecheck yourself, and hold read-only "second opinion" agents to the same evidence bar as implementers
date: 2026-08-16
source: "rrr: call.md (stuck recording recovery + delete feature)"
concepts: [delegation, verification, zcode, agy, second-opinion, autonomous-loop]
---

# Verify delegated agents — including the ones giving "second opinions"

When delegating implementation work to a sibling coding CLI (zcode, agy, or similar), the habit of independently re-running the project's typecheck/build and reading the actual `git diff` before telling the user "done" already existed — and it caught real issues (a delegated agent's report can be truncated or noisy from rate-limit retries and not reflect what was actually shipped).

The gap this session: that same skepticism wasn't applied to a **read-only "second opinion" agent's claims about existing code**. agy asserted (with a file:line citation) that a specific function already existed in the codebase and was the root cause of an observed bug. That claim was relayed to the user as confirmed fact. It was wrong — the function didn't exist until a later delegated implementation run created it fresh.

**Rule**: any claim from a delegated agent — implementer or reviewer — about what code *currently* does or *already* contains needs a direct grep/read check before it's repeated to the user as established fact. "It cited file:line" is not the same as "I checked that line." This applies with equal force to review/diagnosis agents as to implementers, because a second opinion that's wrong but confident is worse than no second opinion — it gets relayed with borrowed authority.

**Secondary pattern reinforced this session**: during an autonomous `/loop`, treat general praise ("good job") as distinct from an explicit instruction naming an irreversible/visible action (commit, restart a live app). Wait for the verb.
