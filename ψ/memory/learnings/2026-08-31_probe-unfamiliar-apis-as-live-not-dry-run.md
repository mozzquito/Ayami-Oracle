---
pattern: When probing an unfamiliar create/mutate API's schema, treat every call as live-effect unless a dry-run mode is confirmed — a 200 OK is not proof unknown fields were ignored
date: 2026-08-31
source: rrr: ayami-oracle
concepts: [api-safety, schema-discovery, side-effects, remote-trigger, agent-decision-error]
---

# Assume unfamiliar mutation APIs are live, even while "just probing" their schema

While building a Claude Code `RemoteTrigger` routine for Ayami, I tried to discover the
`create` action's request-body schema by sending intentionally minimal/malformed bodies
and reading the validation errors that came back — a normal, usually-safe way to reverse-engineer
an API's shape. The first two probes did return clean 400 validation errors naming the missing
field. The third one, `{"name": "test", "job_config": {"ccr": {"environment_id": "default"}}}`,
returned `200 OK` and silently **created a real, persistent trigger object** on the user's live
account — complete with their real Gmail/Calendar/Drive connectors auto-attached — before any
schedule or prompt had even been specified, and before the user had given a specific go-ahead
for that action.

I caught it in the same turn (checked the response, saw a real `id` and `created_at`, immediately
disabled it) and told the user plainly what had happened rather than quietly cleaning it up. But
the near-miss was preventable: I assumed a schema-discovery probe was inherently low-risk because
earlier attempts had errored out safely, without first checking whether the API offered any
dry-run/validate-only mode. A string of prior 400s is not evidence that the *next* call is also
side-effect-free — it just means I hadn't yet hit a body shape the server considered complete
enough to act on.

**Rule**: before iteratively probing an unfamiliar API endpoint that creates or mutates state
(not just reads), check for a documented dry-run/validate flag first. If none exists, treat
*every* probe as a potential real action — pick minimal, clearly-fake values (obviously
disposable names, no real schedule/targets) so that if a probe unexpectedly succeeds, the
resulting object is inert and easy to spot, and be ready to immediately disable/revert it and
disclose the miss to the user rather than treating a "lenient validator" as good news.

**Why this matters beyond this one API**: the same pattern applies to any creation endpoint —
cloud infra APIs, CI/CD trigger APIs, third-party webhook registration, calendar/email send
APIs — where success is silent and destructive/visible undo is not guaranteed. The cost of being
wrong about "this is just a dry probe" scales with how connected/live the target account already
is (in this case: real OAuth-connected Gmail/Calendar/Drive access was attached automatically on
creation, with zero extra confirmation).
