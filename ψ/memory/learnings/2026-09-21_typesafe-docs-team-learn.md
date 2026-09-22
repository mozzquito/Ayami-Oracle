---
pattern: "Learned docs.typesafe.ai as a team: delegated agents over-claim, so re-verify each claim against the cited lines before repeating it"
date: 2026-09-21
source: learn: docs.typesafe.ai
concepts: ["learn", "typesafe", "jev", "multi-agent", "verification", "agy", "zcode", "grokbot"]
---

# Learned docs.typesafe.ai (team run)
- agy called the cookbooks "rigged/deceptive"; re-reading the cited lines showed the biases are disclosed in the docs themselves and it had tied the
  headline 193.6x/444.6x to a cookbook that does not contain them (0 hits in the whole docs). zcode was right that the retry `timeout` is a total
  budget, but wrong that gate.py hides exception types. Delegated findings need line-level verification before they go into notes.
- Slice by line range + read-only flags worked well: agy (gemini-3.1-pro-high, --mode plan) and zcode (--disallowedTools "Edit Write") each returned in a few minutes.
- Grok Bot: send once, keep the messageId, poll with grokbot_verify; never re-send while status is reply_pending.
- Full notes: ψ/learn/docs.typesafe.ai/2026-09-21/0141_TEAM-LEARN.md

## Round 2 (Jev as verifier)
- With zcode+agy writing claims and Jev judging {claim, passage}: 29/33 on Claude's gold; caught contradictions and over-stated wording, but gave a
  false "supported" on a one-digit swap (0.60->0.06) in 2 of 3 runs and missed an implicit calculation. Keep numbers in code; Jev never the only verifier.
- Reviewer-then-experiment loop worked: cross-auditing each other's gold before running and critiquing the interpretation after found my own
  mistakes (Z9 passage window, unfair Choice-vs-Noul comparison). Details: ψ/learn/docs.typesafe.ai/2026-09-21/0141_TEAM-LEARN.md section 7.
