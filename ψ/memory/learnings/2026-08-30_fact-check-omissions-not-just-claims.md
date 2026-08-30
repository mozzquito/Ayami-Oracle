---
pattern: when fact-checking content before publish, verify against primary source and flag omissions, not just check claims for accuracy
date: 2026-08-30
source: rrr: ayami-oracle
concepts: [content-review, fact-checking, verify-before-asserting]
---

# Fact-check omissions, not just claims

Asked to review a draft social post about a tool (Desktop Commander MCP) for
"ความเหมาะสม" (appropriateness) before publishing. Every explicit claim in the draft
was factually correct (checked against the project's own GitHub repo + docs site via
WebSearch/WebFetch). But the draft leaned hard on a privacy/safety framing
("runs 100% locally, nothing uploaded, feel safe") while omitting two facts the
project's own SECURITY.md/docs state plainly: it collects opt-out telemetry, and it
is NOT sandboxed by default (terminal commands bypass its own filesystem blocklist,
full user permissions). Neither omission made any sentence in the draft false — but
both undercut the specific claim the draft was making.

**How to apply**: when reviewing publish-bound content for accuracy, don't just verify
each sentence is true — check the primary source for what the draft *chose not to
mention* that bears directly on the claim being made. The highest-value finding is
often the omission, not a correction. Related: [[feedback_verify_before_asserting]].
