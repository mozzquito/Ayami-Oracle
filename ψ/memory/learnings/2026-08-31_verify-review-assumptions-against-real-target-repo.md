---
pattern: "An abstract external design review (agy/zcode or a separate planning pass) is only as good as what it could see — re-verify its load-bearing assumptions against the real target codebase before treating it as final"
date: 2026-08-31
source: "rrr: ayami-oracle (my-template OSS fork session)"
concepts: ["design-review", "develop-stage", "verification", "zcode", "agy"]
---

# Verify review assumptions against the real target repo before Develop

Designed a schema change (drop a `seq` column, switch to ULID-only ordering) for a fork
of an existing codebase. Got the design reviewed twice, by both `/agy` (Gemini 3.1 Pro)
and `/zcode` (GLM) — both signed off. Implemented it days later during Develop, and
only then, while reading `repo.go` for an unrelated reason, discovered `seq` was
`required` in two OpenAPI specs, rendered by a React component, and asserted by exact
value in several frontend tests. Removing it would have been a much bigger,
contract-breaking change than either reviewer could have known, since neither had the
real target repo open when reviewing an abstract design description.

**Why this happened**: the review prompts described the schema change in prose, not by
pointing the reviewers at the actual files it would touch. A review of a description is
a review of the idea, not a review of its blast radius in the real code.

**How to apply**: when a design has been reviewed abstractly — by another model, or by
yourself in an earlier planning pass — re-verify every load-bearing assumption against
the real target codebase before treating the review as final, especially anything that:
- removes a field or column (grep for its name across the wire contract: OpenAPI specs,
  generated types, frontend components, tests)
- adds a DB-level constraint or trigger (check whether existing test fixtures rely on
  bypassing application-level rules via raw SQL)
- assumes a file or pattern doesn't already exist (never trust an earlier exploration's
  "there's no X here" claim without re-checking right before you'd create X)

Caught in time here because Develop happened to leave enough room to re-derive the same
conclusion from real code before shipping — that's luck plus a verification habit, not
a designed safeguard. The actual fix is to build the real-code check into the review
step itself: hand reviewers (or yourself) the specific files a change touches, not just
a prose description of the change.
