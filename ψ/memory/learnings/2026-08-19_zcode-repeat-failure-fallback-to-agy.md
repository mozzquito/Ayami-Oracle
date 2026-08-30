---
pattern: "When a delegate CLI fails an external-API error already seen this conversation on the identical task, skip the retry and go straight to the proven alternative"
date: 2026-08-19
source: "rrr: ayami-oracle"
concepts: ["delegation", "zcode", "agy", "failover", "reliability"]
---

# Don't retry a delegate CLI blind when you already have direct evidence it will fail the same way

zcode (GLM/z.ai `glm-5-turbo` backend) hit an identical `524 Origin Time-out` from z.ai on the exact same task (`/learn stablyai/orca` code-snippets extraction) twice in one day, across two separate sessions. In the second occurrence, I had *just read the first failure's error* minutes earlier in the same conversation, yet still dispatched zcode again before falling back to agy.

**Rule**: if a delegate CLI (zcode, agy, or any external-API-backed tool) fails with a specific external-service error (5xx, timeout) on a task you already have direct evidence of failing identically earlier in the same conversation, treat that as sufficient signal — route straight to the proven-working alternative instead of spending another full timeout/retry cycle rediscovering it.

This generalizes beyond zcode/agy to any two-backend delegation pattern: the cost of a blind retry is a full round-trip; the cost of checking "did this already fail this way" is one line of reasoning.

Session-metrics context: this is the 4th distinct zcode-reliability friction flavor logged in the last 7 `session-metrics.md` rows as of 2026-08-19 (alias-in-background failure, ~10min slowness, instant-fail+35min-hang, and now a repeat 524 timeout) — flagged as a recurring pattern per parent CLAUDE.md's "same friction 3 sessions → fix root cause" rule.
