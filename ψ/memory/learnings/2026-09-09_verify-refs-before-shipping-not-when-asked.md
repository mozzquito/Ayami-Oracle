---
pattern: Verify every citation URL with an HTTP check before shipping a research deliverable, by default — not only after the user asks if the refs actually work
date: 2026-09-09
source: "rrr: ayami-oracle"
concepts: [research, citations, verification, tor-compliance, sendgrid]
---

# Verify references proactively, not reactively

## What happened

During a TOR-vs-SendGrid compliance research session, the first two research deliverables
(a published web Artifact, then follow-up analysis) shipped with reference URLs taken directly
from WebSearch results — trusted as-is, never independently checked. The user had to explicitly
ask twice ("มี หน้า เว็บ ref ไหม", then later "อยากได้ ref ด้วยว่าทำงานจริงได้") before URL
verification via `curl -I` became part of the workflow. Once adopted, it was cheap (a batch of
`curl -s -o /dev/null -w "%{http_code}"` calls) and caught nothing broken this time — but the
absence of the check was still a real gap in the first two rounds.

## The rule

When a deliverable cites external sources (a compliance matrix, a research memo, anything with
reference links a reader might click), verify every URL resolves (HTTP 200, following redirects)
**before** or as part of the same step that adds it — not as a follow-up remediation once the
user asks. This applies regardless of whether the source is a WebSearch snippet, a WebFetch
result, or a URL recalled from general knowledge.

## Why

- A dead or wrong reference in a procurement/compliance document (like a TOR bid comparison) has
  real downstream cost — someone may cite it in a bid response or contract negotiation.
- The check is nearly free (a batch of HEAD/GET requests), so there's no real tradeoff to defer
  it.
- Users notice the absence and have to ask for it explicitly, which is a signal the default
  should have already covered it.

## How to apply

Any time a task produces content with reference links (artifacts, documents, spreadsheets,
chat responses citing sources) — run a batch `curl` status check on every URL before presenting
or writing them, and only include URLs that return 200. Treat this the same as running a linter
before calling code done: it's a pre-ship check, not an optional add-on.
