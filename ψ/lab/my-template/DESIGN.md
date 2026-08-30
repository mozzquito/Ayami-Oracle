# my-template (มอส's fork) — Design Draft v0.1

Base: [mildronize/my-template](https://github.com/mildronize/my-template) — see analysis in
`ψ/learn/mildronize/my-template/my-template.md`.

Goal: คน (SSO) + AI (API key) ทำงานร่วมกันบนสิทธิ์ของตัวเอง, ทุก mutation ถูกบันทึกแบบ
append-only, และให้ agent ตัวใหม่เข้าใจวิธีคุยกับระบบได้ทันทีผ่าน Skill.

Scope of this draft: 4 deltas จาก base template —
1. Generic `activity_log` (แทน per-domain events table)
2. Scoped API keys (แทน all-or-nothing agent role)
3. CI/CD (base ไม่มีเลย)
4. Agent Skill Template แบบ Claude-Skill (`SKILL.md`) จริง

Everything else (SSO session flow, sqlc+goose DB layer, dual OpenAPI specs, module-first
layout) — **เก็บไว้ตามเดิม**, พิสูจน์แล้วว่าใช้งานได้ในการวิเคราะห์ base repo.

---

## 1. Generic `activity_log`

### ปัญหาของ base

`todo_events` ผูกกับ domain เดียว (`todo_id`, invariant เฉพาะ todo). เพิ่ม domain ใหม่ =
copy ตาราง + invariant ใหม่ทุกครั้ง. ไม่มีที่เดียวสำหรับดู "ทั้งระบบเพิ่งเกิดอะไรขึ้นบ้าง"
ข้าม domain.

### Schema

```sql
CREATE TABLE activity_log (
    id                 TEXT PRIMARY KEY,           -- ULID (sortable by time, unlike UUIDv4)
    entity_type        TEXT NOT NULL,               -- 'todo', 'project', 'api_key', ... (no FK, polymorphic by design)
    entity_id          TEXT NOT NULL,
    actor_id           TEXT NOT NULL,               -- FK users(id)
    actor_kind         TEXT NOT NULL,               -- 'human' | 'agent' — denormalized from users.kind at write time
                                                     -- so filtering "AI ทำอะไรบ้าง" never needs a join
    action             TEXT NOT NULL,               -- 'created' | 'updated' | 'status_changed' | 'commented' | 'assigned' | 'field_changed' | 'deleted'
    payload            TEXT,                        -- JSON: structured diff/snapshot {"field":"status","from":"open","to":"done"}
    body               TEXT,                        -- freeform (comments)
    seq                INTEGER NOT NULL,             -- monotonic per (entity_type, entity_id) — computed inside the write transaction
    client_request_id  TEXT NOT NULL UNIQUE,         -- idempotency key, every write call must send one
    created_at         TIMESTAMP NOT NULL
);

CREATE UNIQUE INDEX idx_activity_entity_seq ON activity_log (entity_type, entity_id, seq);
CREATE UNIQUE INDEX idx_activity_idempotency ON activity_log (client_request_id);
CREATE INDEX idx_activity_feed ON activity_log (created_at DESC, id DESC);
CREATE INDEX idx_activity_actor ON activity_log (actor_id, created_at DESC);
CREATE INDEX idx_activity_entity ON activity_log (entity_type, entity_id, seq);
```

### Invariants (numbered so agents can cite them, mirroring base repo's I-style)

| # | Rule |
|---|------|
| A1 | Single write path: every domain service calls `ActivityLog.Append(...)`, no direct `INSERT INTO activity_log` anywhere else in the codebase. |
| A2 | Append-only: no UPDATE/DELETE on `activity_log`, enforced by convention + a test that greps for forbidden statements against this table. |
| A3 | `seq` computed as `max(seq)+1` for that `(entity_type, entity_id)` inside the same DB transaction as the domain-state write — both succeed or both roll back. |
| A4 | Idempotency: duplicate `client_request_id` returns the existing row, writes nothing new. |
| A5 | `actor_kind` is derived server-side from the resolved identity, never accepted from the client. |

### Design decision: state tables stay separate from the log

`activity_log` is **history only**, not the source of truth for current state. Each
domain keeps its own state table (e.g. `todos` with a `status` column) exactly like the
base repo. A mutation writes to both the domain table and `activity_log` in one
transaction via the shared `Append()` call. This avoids full event-sourcing (no need to
replay history to compute current state) while still getting one unified audit trail.

**Tradeoff accepted**: `payload` is untyped JSON per action, so cross-domain queries on
*content* (not just entity_type/action/actor) need app-level parsing. Acceptable — the
win (one shared table, one shared invariant set, zero boilerplate per new domain)
outweighs losing column-level typing on the log itself.

### API surface

```
GET /api/v1/activity?entity_type=&entity_id=&cursor=&limit=   # cross-entity feed, or scoped to one entity
GET /api/v1/{entity_type}/{id}/activity                       # convenience: per-entity timeline, oldest-first
```

Every domain's write endpoints (`POST /todos`, `PATCH /todos/{id}`, etc.) require
`clientRequestId` in the request body — same contract as base repo's todo_events, just
generalized.

---

## 2. Scoped API keys

### ปัญหาของ base

Agent key = สิทธิ์เท่ากันหมดในระดับ role (`agent`). ไม่มีทางออก key ที่ "อ่านได้อย่างเดียว"
หรือ "เขียนได้เฉพาะ todos ห้ามแตะ keys" — agent ทุกตัวมีอำนาจเท่ากัน ซึ่งขัดกับเป้าหมาย
"แยกให้ได้ว่าใครทำหน้าที่อะไร"

### Schema

```sql
ALTER TABLE api_keys ADD COLUMN label            TEXT NOT NULL DEFAULT '';   -- human-readable, e.g. "deploy-bot"
ALTER TABLE api_keys ADD COLUMN status            TEXT NOT NULL DEFAULT 'active'; -- 'active' | 'paused' | 'revoked'
ALTER TABLE api_keys ADD COLUMN paused_at         TIMESTAMP;
ALTER TABLE api_keys ADD COLUMN rate_limit_per_min INTEGER;                 -- NULL = use system default

CREATE TABLE api_key_scopes (
    api_key_id  TEXT NOT NULL REFERENCES api_keys(id),
    scope       TEXT NOT NULL,     -- '<action>:<resource>', e.g. 'read:todos', 'write:todos', 'write:activity_log'
    PRIMARY KEY (api_key_id, scope)
);
```

Scope format: `action:resource` — `read`, `write`, or `admin`; resource is a domain name
or `*`. `admin:keys` reserved for owner-issued management keys (list/revoke other keys).
No key may hold `admin:*` unless explicitly granted at issuance — CLI still the only
issuance path.

### Middleware change

```go
// existing: RequireActor resolves identity (unchanged)
// new: wraps it, checked after actor resolution, before handler
func RequireScope(scope string) gin.HandlerFunc {
    return func(c *gin.Context) {
        actor, _ := ActorFromContext(c)
        if !actor.HasScope(scope) {          // owner/session bypasses scope checks entirely (I2 still applies: Bearer→owner is still illegal)
            respondForbidden(c, "missing_scope")
            return
        }
        c.Next()
    }
}

// route registration
router.POST("/todos", RequireActor, RequireScope("write:todos"), handler.CreateTodo)
```

Scopes load once at key-resolution time (already fetching the `api_keys` row; scopes
join costs one extra indexed query, cached on `actor` for the request lifetime) — no
added DB roundtrip per scope check.

### Pause vs revoke

- `paused`: temporary, reversible by owner, request returns `423 { "error": "key_paused" }`. For "หยุด agent นี้ชั่วคราวเดี๋ยวดูให้" without losing the key.
- `revoked`: permanent, same as base repo today (`401`).

### Rate limiting

Token-bucket per `api_key_id`, in-memory (single-instance SQLite template — no Redis
dependency for v1). Default from env `DEFAULT_RATE_LIMIT_PER_MIN`, override via
`rate_limit_per_min` column. `429` with `Retry-After` header on exceed. Documented in the
Agent Skill (§4) so agents back off instead of hammering.

### Issuance CLI change

```bash
cmd/issue-key --handle deploy-bot --scope write:todos --scope write:activity_log --rate-limit 60
```

Still CLI-only (keeps I8 from base: raw key never crosses HTTP).

---

## 3. CI/CD

Base repo has zero `.github/workflows/`. Minimum for an open-source template (contributors
need feedback on PRs, and forks need a working example to copy):

`.github/workflows/ci.yml` — on `push` + `pull_request`:

```yaml
jobs:
  backend:
    steps:
      - go vet ./...
      - make generate && git diff --exit-code   # codegen must not drift from committed output
      - go build ./...
      - go test ./...
  frontend:
    steps:
      - npm ci
      - npm run typecheck
      - npm run test
      - npm run build
  e2e:                                            # optional: only on main, or manual dispatch
    if: github.ref == 'refs/heads/main'
    steps:
      - docker compose -f e2e/docker-compose.yml up -d   # local Hydra
      - make e2e
```

Not in v1 (defer): Docker image publish on tag, `gosec`/`npm audit` — nice-to-have, add
once the template stabilizes, not a blocker for open-sourcing.

---

## 4. Agent Skill Template (Claude-Skill format)

Base repo has `.agents/agents/chief-agent.md` — a Chief/Builder/Tester **workflow-role**
doc, not a portable `SKILL.md`. Add a real Claude Skill inside the template repo itself so
any agent (Claude Code, agy, zcode) that clones/forks it gets working instructions without
reading the whole codebase first.

`.claude/skills/my-template-api/SKILL.md`:

```markdown
---
name: my-template-api
description: Call this repo's HTTP API as an authenticated agent — auth header, idempotency, scopes, rate limits, and the activity log contract. Use whenever writing code that calls this service's own API from an agent/script identity.
---

# Calling the API as an agent

## Auth
`Authorization: Bearer <api_key>` — get a key via `cmd/issue-key` (ask the owner to run it;
agents cannot issue their own keys). Key format: `tpl_<prefix>_<secret>`.

## Every write call needs a client_request_id
Generate a UUIDv4 per *logical* action (not per HTTP retry — reuse the same id when
retrying the same action). The server treats duplicates as no-ops and returns the
original result (see activity_log invariant A4).

## Scopes
Your key has fixed scopes (`GET /api/v1/me` shows them). A 403 with
`{"error":"missing_scope"}` means you need a different key — ask the owner, don't try to
work around it.

## Rate limits
429 means back off — respect `Retry-After`. Don't retry in a tight loop.

## Reading history
`GET /api/v1/{entity_type}/{id}/activity` — per-entity timeline, oldest-first.
`GET /api/v1/activity?entity_type=&cursor=&limit=` — cross-entity feed, newest-first.

## Invariants you must not try to violate
- I2 / A5: you cannot become 'owner' or spoof actor_kind — don't try.
- Terminal actions (e.g. closing/deleting) are owner-only by design in most domains — a
  403 there is expected, not a bug to route around.
```

This SKILL.md ships **in the template repo**, not in a personal `~/.claude/skills/` — so
every fork carries it, and any agent working on (or against) the forked service picks it
up automatically.

---

## Open questions before moving to Develop

1. ULID vs UUID for `activity_log.id` and other PKs — ULID gives free time-sortability,
   base repo uses plain UUID/TEXT ids today. Worth the extra dependency?
2. Rate limiter: in-memory is fine for a single instance — confirm the template stays
   single-instance (no horizontal scaling requirement) before committing to that vs Redis.
3. Scope granularity: per-domain (`write:todos`) vs per-action (`write:todos.status`) —
   draft above picks per-domain for simplicity; revisit if a real use case needs finer
   control.
