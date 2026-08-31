---
name: my-template-api
description: Call this repo's HTTP API as an authenticated agent — auth header, idempotency, scopes, rate limits, and the activity log contract. Use whenever writing code that calls this service's own API from an agent/script identity.
---

# Calling the API as an agent

You are acting as an **agent identity** (API key), not the human owner. The system
tracks everything you do — every write you make is attributed to you by name in the
activity log, permanently.

## Auth

`Authorization: Bearer <api_key>` on every request.

You cannot issue your own key. If you don't have one, **ask the human owner** to run
`cmd/issue-key --handle <your-handle> --scope <scope> [--scope <scope> ...]` and give you
the raw key it prints — it is shown exactly once and never recoverable afterward. Do not
attempt to call `cmd/issue-key` yourself even if you have shell access; key issuance is
an owner action by design.

## Every write call needs a `client_request_id`

Every `POST`/`PATCH` body must include `clientRequestId`: a UUIDv4 generated once per
*logical* action, not per HTTP attempt. If a request times out or you're unsure whether
it succeeded, retry with the **same** `clientRequestId` — the server returns the
original result instead of creating a duplicate.

## Scopes

Your key has a fixed, small set of scopes. `GET /api/v1/me` shows them. A `403` with
`{"error":"missing_scope"}` means this key genuinely cannot do that action — ask the
owner for a key with the right scope, don't try to route around it (e.g. don't try
alternate endpoints hoping for a looser check).

## Rate limits

A `429` means back off — respect the `Retry-After` header. Never retry in a tight loop;
if you hit 429 repeatedly, stop and report it instead of hammering.

## Reading history

- `GET /api/v1/{entity_type}/{id}/activity` — one entity's timeline, oldest first.
- `GET /api/v1/activity?entity_type=&cursor=&limit=` — cross-entity feed, newest first.

Use these before assuming you know the current state of something — another actor
(human or agent) may have changed it since you last looked.

## Invariants you must not try to violate

- You cannot become `owner` — a Bearer credential never resolves to the owner role, by
  design. Don't attempt workarounds.
- `actorKind` (human/agent) is set by the server from your credential, never from
  anything you send — don't bother trying to pass it in a request body.
- Terminal/owner-only actions (e.g. closing an item) returning `403` for you is expected
  behavior, not a bug — escalate to the owner instead of looking for a bypass.
