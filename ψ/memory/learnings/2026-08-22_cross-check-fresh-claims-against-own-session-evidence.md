---
pattern: "When a fresh document or delegated-agent claim contradicts something already empirically observed earlier in the same session, treat the empirical observation as higher-confidence by default and re-verify the new claim — don't let recency alone decide which source wins."
date: 2026-08-22
source: "rrr: ayami-oracle"
concepts: ["verification", "self-review", "reconcile", "sendgrid-api", "sibling-agent-consult"]
---

# Learned: cross-check fresh claims against your own session's evidence

## What happened
While building `ψ/lab/sendgrid-log-poc/reconcile.ts`, I picked `sg_message_id_created_at`
as the time-filter field name for SendGrid's Filter Messages API — sourced from a
WebFetch doc-summary. The first real run failed with 24 straight `400 unknown identifier`
errors. The correct field name, `last_event_time`, had already appeared in this exact
session's own earlier `curl` output against the live API — I had printed it in a JSON
response a while before writing `reconcile.ts`, but didn't check my own prior evidence
against the new doc claim before using it in code.

## Why it happened
A freshly-fetched document felt more authoritative than something I'd already seen
earlier in the conversation, purely because it was the thing I looked at most recently
while writing that specific piece of code. Recency of *retrieval* got treated as a proxy
for confidence, when it isn't one — direct empirical observation (a real API response)
outranks a secondary document summary regardless of which one I consulted last.

## What to do instead
- Before using a fact from a newly-fetched document (API docs, a delegated agent's
  answer, a web search summary) in code or a decision, do a quick mental (or literal
  grep) check: "have I already seen the real, empirical version of this fact earlier in
  this session?"
- If yes, and the two disagree, the empirical observation wins by default — re-verify
  the document claim rather than overwriting what you already confirmed firsthand.
- This applies equally to delegated sibling-agent calls (zcode/agy): two stateless calls
  on related questions within one session have no memory of each other, so a later
  call's answer contradicting an earlier, already-agreed answer is not automatically an
  update — read both side by side before adopting the newer one. See also this same
  session's separate instance of this: zcode later recommended Lambda for a webhook
  receiver, silently contradicting a cold-start conclusion zcode and agy had already
  reached together earlier — caught by comparing outputs rather than trusting the latest
  one by default.

## Related
[[verify-before-asserting]] — general pattern of checking evidence before stating
conclusions; this is the specific case where the evidence was already in-hand and just
needed to be recalled rather than freshly gathered.
