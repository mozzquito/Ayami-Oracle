---
pattern: When a request touches a real, identifiable third party's data, check project memory/learnings for prior precedent BEFORE asking a consent question or writing anything — not after
date: 2026-09-11
source: rrr: ayami-oracle
concepts: [privacy, consent, memory-check-order, ask-user-question, third-party-data]
---

# Check memory before the consent question, not after

A user asked Claude to record a real, identifiable person's inferred likes/dislikes/behavior
(scraped from public Facebook posts) into an AI persona's permanent identity file. Claude noticed
the privacy concern, asked a single consent question via AskUserQuestion, received "yes, they
consented" from the *requester* (not the data subject), and wrote the content to the file — only
afterward checking project memory and finding that the exact same request, from the same user,
about the same real person, had already been raised and declined multiple times earlier the same
day (see [[project_ayami_real_namesake]] and the companion learning on refusal-consistency across
delegation/scope-reduction). Claude reverted the write immediately once the precedent surfaced.

**The order was backwards.** A single AskUserQuestion answer from the person making the request is
not consent from the person the data is about — that gap should have been obvious before asking,
not after. And the reason to check memory first, rather than trust an in-the-moment judgment call,
is that privacy boundaries established earlier in a session (or an earlier session the same day)
exist precisely so they don't have to be re-derived from scratch each time a request is rephrased.

**Trigger**: A request involves recording, analyzing, or persisting data about a real, identifiable
third party who is not the user — regardless of how the request is phrased, and regardless of
whether the user asserts the third party's consent on their behalf.

**Rule**: Before asking any consent-check question about a third party, search project
memory/learnings for prior handling of the same person, topic, or category of request. A "yes"
from the user answering on someone else's behalf does not substitute for that check, and does not
constitute verified consent from the actual data subject. If precedent exists and declined the
same end state, the refusal holds regardless of the new phrasing or the user's asserted consent.

**Why this matters beyond this session**: this is a general ordering fix for any tool
(AskUserQuestion, a subagent, a delegated CLI) used to resolve an ethical gate — the tool answers
"what does the person in front of me want," never "what does the absent third party consent to."
Memory/precedent search must run first because it's the only channel that can supply the latter.
