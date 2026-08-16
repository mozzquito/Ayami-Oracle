---
pattern: When multiple concurrent sessions serve the same human, an out-of-context question may belong to a sibling session — actively check shared state (vault, memory) before inferring which one from recall alone
date: 2026-08-09
source: rrr: ayami-oracle
concepts: [concurrent-sessions, verify-before-asserting, shared-state, memory-search]
---

# Check shared state before answering cross-session questions

Boss sent "geotrust หรือเปล่า" with no antecedent in this conversation. Ayami correctly avoided fabricating a certificate-related answer, and correctly inferred (from a diary entry and a session-metrics table already in context) that the question probably belonged to a different, concurrent session investigating a DigiCert cert. That inference turned out right — but it was built entirely from what was already sitting in context, not from an active check of shared state (grepping the vault, searching auto-memory) that could have turned "probably" into "confirmed" before replying.

**The generalizable pattern**: this is a specific instance of "verify before asserting" (already a recurring theme — see session-metrics rows for 2026-08-09 14:23 and 15:01), applied to the concurrent-session case specifically. When several Claude Code sessions serve one human in parallel, a question that seems unrelated to *this* session's history is not evidence the human made a mistake — it's a signal to check whether shared state (memory, vault, logs another session may have written) has the missing context, before either fabricating an answer or shrugging and asking the human to re-explain everything from scratch.

**Rule**: when a request doesn't connect to anything in the current session's own history, before replying: (1) do a cheap active check of shared state — grep the vault for the topic, check auto-memory, look for sibling-session artifacts (session-metrics.md, recent retros) — and (2) only then form the reply, stating clearly what was confirmed vs. inferred. This costs seconds and converts a hedge into either a confirmed answer or a more precise clarifying question ("I found session X was investigating this — is that the one you mean?") instead of a generic "can you clarify?"

**Related**: [[2026-08-09_ask-before-mapping-onto-repos-own-conventions]] (same day, same session — a different flavor of "check before assuming"). Also ties to the existing `feedback_verify_before_asserting.md` auto-memory entry and the `2026-08-08_session-detection-breaks-under-concurrent-forks.md` learning — concurrent sessions are a recurring source of this class of error across multiple distinct mechanisms (dig-miner file selection, cross-session question routing, shared vault writes).
