# my-template (มอส's fork) — Design Draft v0.2

> v0.2: revised after cross-check from `/agy` (Gemini 3.1 Pro) and `/zcode` (GLM) — see
> **§5 Review synthesis** at the bottom for what changed and why.

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
    id                 TEXT PRIMARY KEY,           -- ULID: time-sortable, doubles as ordering key (see A3 below — no seq column)
    entity_type        TEXT NOT NULL,               -- 'todo', 'project', 'api_key', ... (no FK, polymorphic by design)
    entity_id          TEXT NOT NULL,
    actor_id           TEXT NOT NULL,               -- FK users(id)
    actor_kind         TEXT NOT NULL,               -- 'human' | 'agent' — denormalized from users.kind at write time
                                                     -- so filtering "AI ทำอะไรบ้าง" never needs a join
    action             TEXT NOT NULL,               -- 'created' | 'updated' | 'status_changed' | 'commented' | 'assigned' | 'field_changed' | 'deleted'
    payload            TEXT,                        -- JSON: structured diff/snapshot {"field":"status","from":"open","to":"done"} — small, not a raw request dump
    body               TEXT,                        -- freeform text only (comments) — never a full request/response body
    client_request_id  TEXT NOT NULL UNIQUE,         -- idempotency key, every write call must send one
    created_at         TIMESTAMP NOT NULL
);

-- no separate index needed for client_request_id: the column-level UNIQUE constraint
-- above already creates one in SQLite (flagged by review — was redundant in v0.1/early v0.2)
CREATE INDEX idx_activity_feed ON activity_log (created_at DESC, id DESC);
CREATE INDEX idx_activity_actor ON activity_log (actor_id, created_at DESC);
CREATE INDEX idx_activity_entity ON activity_log (entity_type, entity_id, id);  -- id (ULID) gives per-entity order, no seq needed

-- A2 enforced at the DB level, not just by convention:
CREATE TRIGGER trg_activity_log_no_update
BEFORE UPDATE ON activity_log
BEGIN SELECT RAISE(ABORT, 'activity_log is append-only'); END;

CREATE TRIGGER trg_activity_log_no_delete
BEFORE DELETE ON activity_log
BEGIN SELECT RAISE(ABORT, 'activity_log is append-only'); END;
```

### Invariants (numbered so agents can cite them, mirroring base repo's I-style)

| # | Rule |
|---|------|
| A1 | Single write path: every domain service calls `ActivityLog.Append(...)`, no direct `INSERT INTO activity_log` anywhere else in the codebase. |
| A2 | Append-only: enforced by DB triggers (`trg_activity_log_no_update/delete`), not just convention — a rogue `UPDATE`/`DELETE` fails at the DB, doesn't just fail code review. |
| A3 | Ordering — per-entity and global — comes from the ULID `id` (time-sortable by construction), not a separate `seq` counter. Dropped the original per-entity `seq` column: it required `MAX(seq)+1` inside every write transaction, which is a real contention point under concurrent writers to the same entity, for a guarantee ULID already gives for free. |
| A4 | Idempotency: duplicate `client_request_id` returns the existing row, writes nothing new. **Implementation note**: SQLite's `INSERT ... ON CONFLICT DO NOTHING RETURNING *` does NOT return the pre-existing row on conflict (only newly-inserted rows). `Append()` must catch the unique-constraint error and issue an explicit `SELECT ... WHERE client_request_id = ?` fallback. |
| A5 | `actor_kind` is derived server-side from the resolved identity, never accepted from the client. |

**Deferred, not forgotten**: `ip_address`/`user_agent` columns for security-review context, and a `workspace_id`/tenant column for multi-tenant future-proofing — both real suggestions from the review, both skipped in v0.2 because the current goal is still single-owner/single-tenant. Add them as nullable columns in a later migration if/when they're actually needed; retrofitting a nullable column later is cheap, so this isn't a one-way door.

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
ALTER TABLE api_keys ADD COLUMN label             TEXT NOT NULL DEFAULT '';   -- human-readable, e.g. "deploy-bot"
ALTER TABLE api_keys ADD COLUMN status             TEXT NOT NULL DEFAULT 'active'; -- 'active' | 'paused' | 'revoked'
ALTER TABLE api_keys ADD COLUMN scopes             TEXT NOT NULL DEFAULT '[]'; -- JSON array, e.g. ["write:todos","write:activity_log"]
ALTER TABLE api_keys ADD COLUMN rate_limit_per_min INTEGER;                  -- NULL = use system default
ALTER TABLE api_keys ADD COLUMN last_used_at       TIMESTAMP;                -- updated (best-effort, async) on each successful auth
```

**Scopes live as a JSON column on `api_keys`, not a separate `api_key_scopes` table** —
changed from v0.1 per review feedback. The scope set per key is small (a handful of
strings), already fetched in full on every request as part of the `api_keys` row lookup,
and never queried independently ("find all keys with scope X" is an admin-rarity, not a
hot path) — a join table buys query-ability nothing here actually needs, at the cost of
an extra query on every request.

**No `paused_at` column** — a pause/resume/revoke transition is itself an event, so it's
written to `activity_log` (`entity_type='api_key', action='paused'|'resumed'|'revoked'`)
instead of a dedicated timestamp column. `status` still lives on `api_keys` for fast
lookup; *when* it last changed and *who* changed it comes from the log, for free, instead
of adding parallel bookkeeping.

Scope format: `action:resource` — free-form string, not a closed enum. Convention is
coarse per-domain (`read:todos`, `write:todos`) by default; a domain that genuinely needs
a finer split (e.g. `close:todos` separate from `write:todos`) can mint a new scope string
without a schema change. `admin:keys` reserved for owner-issued management keys
(list/revoke other keys). No key may hold `admin:*` unless explicitly granted at
issuance — CLI still the only issuance path.

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

Scopes come straight off the `actor.Scopes` field already parsed from the `api_keys` row
during identity resolution — zero extra DB roundtrip per scope check (this is the direct
payoff of storing scopes as JSON on the row instead of a join table).

### Pause vs revoke

- `paused`: temporary, reversible by owner, request returns `423 { "error": "key_paused" }`. For "หยุด agent นี้ชั่วคราวเดี๋ยวดูให้" without losing the key. Writes `activity_log(entity_type='api_key', action='paused')`.
- `revoked`: permanent, same as base repo today (`401`). Writes `activity_log(..., action='revoked')`.

### Rate limiting

Token-bucket per `api_key_id`, in-memory (single-instance SQLite template — no Redis
dependency for v1; `golang.org/x/time/rate` is enough, zero extra infra). Default from env
`DEFAULT_RATE_LIMIT_PER_MIN`, override via `rate_limit_per_min` column. `429` with
`Retry-After` header on exceed. Documented in the Agent Skill (§4) so agents back off
instead of hammering.

**Added per review**: a per-key limit alone doesn't cap total load — N keys at 60/min each
is N×60/min with no ceiling. Add a second, process-wide token bucket
(`GLOBAL_RATE_LIMIT_PER_MIN` env, generous default) that every request also draws from,
regardless of which key it used. Implement both as the same `RateLimiter` interface so a
future swap to a shared backend (Redis, if the template ever goes multi-instance) is a
single implementation swap, not a call-site rewrite.

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
      - golangci-lint run                          # added per review — go vet alone catches very little
      - go mod tidy && git diff --exit-code go.mod go.sum   # added per review — catch un-tidied deps
      - make generate && git diff --exit-code      # codegen must not drift from committed output
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
      - make e2e   # self-contained: Playwright's global-setup.ts/global-teardown.ts already
                   # run `docker compose up`/`down -v` against e2e/docker-compose.yml —
                   # verified in base repo source, no separate compose step needed in CI
```

Not in v1 (defer): Docker image publish on tag, `gosec`/`npm audit` — nice-to-have, add
once the template stabilizes, not a blocker for open-sourcing.

The actual workflow file is drafted at `ψ/lab/my-template/scaffold/.github/workflows/ci.yml`
in this repo, ready to copy into the real fork.

---

## 4. Agent Skill Template (Claude-Skill format)

> **Correction, made during Develop (2026-08-31)**: this section originally claimed the
> base repo had *no* portable `SKILL.md`, only `.agents/agents/chief-agent.md`. That was
> wrong — the initial `/learn` exploration (a Haiku sub-agent) missed it. The base repo
> actually ships a genuinely excellent
> `.claude/skills/my-template-api/SKILL.md` (303 lines) plus
> `references/endpoints.md` and `references/errors.md`, covering auth, all invariants
> (I1/I2/I3/I5/I8/I13/I14/I18/I19), the key-resolver footgun, and worked curl examples.
> During Develop this was almost silently overwritten by a blind `cp` of the scaffold
> file below — caught via `git status`/`git diff` before committing, restored from HEAD.
> **Decision: extend the existing file in place once §1/§2 are implemented (so it
> documents real new behavior — scopes, the generic activity feed), don't replace it.**
> The scaffold below is kept as the original draft for reference, not as what actually
> ships.

Base repo has `.agents/agents/chief-agent.md` — a Chief/Builder/Tester **workflow-role**
doc, not a portable `SKILL.md`. Add a real Claude Skill inside the template repo itself so
any agent (Claude Code, agy, zcode) that clones/forks it gets working instructions without
reading the whole codebase first.

`.claude/skills/my-template-api/SKILL.md` (abbreviated below — full version, with the
"ask the owner, don't self-issue keys" point agy flagged, is in the scaffold file):

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
up automatically. Actual file drafted at
`ψ/lab/my-template/scaffold/.claude/skills/my-template-api/SKILL.md` in this repo.

**Known staleness risk (flagged in review, not fixed in v0.2)**: this doc will drift from
the real routes/scopes as the API evolves. Worth a follow-up CI check later (e.g. a
smoke test that greps SKILL.md's documented endpoints against the OpenAPI spec) — not
blocking for the first version, tracked here so it isn't forgotten.

---

## 5. Review synthesis

Draft v0.1 was cross-checked with `/agy` (Gemini 3.1 Pro, `--mode plan`) and `/zcode`
(GLM) before starting Develop, per the project's SDLC-gate convention. `zcode` initially
failed twice with a generic file-read error unrelated to this design (see
`ψ/memory/learnings/2026-08-31_zcode-file-read-turn-execution-failed.md`) — worked around
by pasting the design inline instead of pointing it at the file.

**Where both agreed (adopted directly):**
- Drop the per-entity `seq` counter — ULID's time-sortable `id` already gives ordering,
  and `MAX(seq)+1` inside every write transaction is a real contention point for a
  guarantee that was free otherwise. → §1, A3.
- Keep ULID (not UUID) for all new IDs.
- Keep the rate limiter in-memory, not Redis, for this template's single-instance scope.
- The `ON CONFLICT DO NOTHING RETURNING *` idempotency pattern doesn't return the
  existing row in SQLite — needs an explicit fallback `SELECT`. → §1, A4 implementation note.

**Where they disagreed (resolved by picking a rationale, not a vote):**
- agy: scopes should be a JSON column, not a join table (simplicity). zcode: didn't object
  to the join table but wanted finer-grained scopes than `read/write/admin`. **Resolved**:
  adopted agy's JSON-column storage (real simplification, no downside at this scale) *and*
  kept the scope string itself free-form (not a closed enum) so finer verbs are possible
  without a schema change — satisfies zcode's concern without agy's join-table cost. → §2.
- agy suggested moving the skill to `.agents/skills/` — **rejected**: `.claude/skills/<name>/SKILL.md`
  is Claude Code's actual load path; moving it would make Claude Code stop discovering the
  skill. Kept as-is.

**Accepted but deferred (not v0.2, tracked for later):**
- `ip_address`/`user_agent` on `activity_log`, `workspace_id` for multi-tenant — real
  suggestions, skipped because the current goal is still single-owner/single-tenant.
- `golangci-lint` + `go mod tidy` in CI — adopted, see §3.
- `last_used_at` on `api_keys` — adopted, see §2.
- A global (not just per-key) rate-limit ceiling — adopted, see §2.
- SKILL.md drift-check in CI — flagged, not built yet, see §4.

### Round 2 — final verification pass on v0.2 + scaffold files

Ran a second pass with both reviewers, this time checking v0.2 itself (not just v0.1)
plus the two scaffold files, before calling this "ready for Develop."

**agy (re-check of v0.2 + scaffold files):**
- ✅ Confirmed §5's representation of its own earlier feedback is accurate.
- ✅ Caught a real redundancy: `client_request_id TEXT NOT NULL UNIQUE` already gets an
  auto-created unique index in SQLite — the separate `CREATE UNIQUE INDEX
  idx_activity_idempotency` was dead weight. **Fixed** — removed, replaced with a comment.
- ❌ Flagged the `e2e` job in `scaffold/.github/workflows/ci.yml` as missing a `docker
  compose up` step. **Checked against the actual base repo source before accepting**:
  `e2e/global-setup.ts` / `global-teardown.ts` in mildronize/my-template already run
  `docker compose up`/`down -v` against `e2e/docker-compose.yml` themselves, invoked by
  Playwright's `globalSetup` hook — so `make e2e` is self-contained. **Not applied** — the
  scaffold file was already correct; the DESIGN.md §3 *pseudocode* was the stale one
  (leftover from before this was verified), now fixed to match reality instead.

**zcode (re-check of the revised activity_log + api_keys schema, pasted inline — file-read
still broken per the earlier learning, worked around the same way):**
- ✅ `BEFORE UPDATE/DELETE ... RAISE(ABORT, ...)` triggers are correct SQLite syntax, fire
  reliably against Go's `database/sql` (surfaces as a normal wrapped `SQLITE_CONSTRAINT`
  error), and `ABORT` (not `FAIL`) is the right conflict mode for this pattern.
- ✅ Tracking api_key status transitions purely via `activity_log` rows (no `paused_at`
  column) is sound — flagged one real implementation detail to carry into Develop: write
  the `activity_log` row *before* the `api_keys.status` update inside the transaction, so
  a partial failure can't leave a state change with no audit trail.
- Suggested widening `idx_activity_entity` to `(entity_type, entity_id, created_at DESC, id
  DESC)`. **Evaluated, not applied**: the whole point of switching to ULID (§1, A3) is
  that `id` already sorts chronologically, so an index on `(entity_type, entity_id, id)`
  already satisfies `ORDER BY id` for the per-entity timeline directly — adding
  `created_at` to the index would just duplicate information the `id` column already
  encodes, for a query pattern (`GET /{entity_type}/{id}/activity`, oldest-first) that
  base repo's own docs describe as sorted by the monotonic key, not wall-clock time.

---

## Status: shipped — v1.0 built, tested, pushed (2026-08-31)

Forked for real: **https://github.com/mozzquito/my-template** (private). Local working
copy at `ψ/incubate/my-template/` in this repo (gitignored, has its own `.git`).

All 4 deltas are live on `main` there, each its own reviewed commit:

1. `1f8c48a` Import from mildronize/my-template (baseline, MIT license/attribution kept)
2. `7c3ed51` Rename module path to github.com/mozzquito/my-template
3. `95c824f` Add CI workflow
4. `946d263` Generalize todo_events into a shared activity_log table
5. `f5e0b13` Add scoped, pausable API keys

**What changed from this design doc once real code got involved** (Develop-stage
corrections, all in the commits' own messages, summarized here):

- **Kept `seq`, didn't switch to ULID-only ordering.** §1's ULID decision (validated by
  both reviewers) turned out to be moot once the real code showed `seq` is load-bearing
  all the way through `openapi.yaml`/`bff-openapi.yaml` (both mark it `required`),
  `TimelineEventRow.tsx`, and several `web/src` tests asserting exact values. Ripping it
  out would have been a much bigger, contract-breaking change for a contention concern
  that doesn't materialize at this template's realistic write volume. Table renamed to
  `activity_log` with `entity_type`/`entity_id` as designed; `seq` computation and plain
  UUID ids (matching the codebase's existing `google/uuid` convention everywhere) kept
  as-is.
- **Reverted the DB-level append-only trigger.** Added it per the design, then found
  `internal/domain/todo/repo_test.go` legitimately backdates `created_at` via raw `UPDATE`
  for cursor-pagination test fixtures — an unconditional trigger can't tell that apart
  from a real attempt to rewrite history. Reverted to application-level-only enforcement,
  which is what the base repo's own `todo_events` had *deliberately* chosen already
  (its own comment said so) — a design review made without reading that comment first.
- **Scoped-down keys don't reset to full access on rotation.** Not in the original design
  at all — found while writing tests (`TestRotateWithScopes_NilPreservesExistingKeysScope`)
  that `Rotate`'s original shape would have silently widened a narrowed key back to `*:*`
  every time it rotated. Fixed before it ever shipped.
- **The "Agent Skill Template" delta was already half-done by the base repo.** Discovered
  mid-Delta-1 that `.claude/skills/my-template-api/SKILL.md` (303 lines, genuinely
  excellent) already existed — the original `/learn` pass missed it. Extended it (scopes,
  pause, two new error codes) instead of writing a fresh one from the §4 scaffold.
- **Generic `activity_log` stayed single-owner in `dbquery.TableOwnership`.** The base
  repo's own architecture tests (`internal/architecture_test.go`'s I15 check,
  `internal/dbquery/tableisolation.go`'s table-ownership model) assume one table = one
  owning domain module. Making the table *literally* multi-writer today would have meant
  redesigning that enforcement for a second domain that doesn't exist yet. `todo` stays
  the sole declared owner; the win delivered now is the *shape* (entity_type/entity_id,
  no domain-specific event table needed) — a real second domain reusing the table is a
  future fork's own `TableOwnership` update, not blocked by anything built here.

**Deferred, explicitly, not forgotten:** rate limiting (per-key and global) from §2 was
scoped out of this Develop pass — schema/scope/pause landed and are tested; a token-bucket
middleware needs its own careful test pass this session didn't have room for. Also
deferred: `ip_address`/`user_agent` on `activity_log`, multi-tenant `workspace_id`,
SKILL.md drift-check in CI, Docker image publish, `gosec`/`npm audit`.

**Verification**: every commit has `go build/vet/test` green, `gofmt` clean, and (where the
change could touch it) `web`'s `npm run typecheck` + `npm test` green — recorded in each
commit message, not just asserted here.

**Not done yet**: Hydra/SSO client registration (`docs/GETTING-STARTED.md` Step 1) —
needs a real IdP and มอส's own input, out of scope for an unattended session. The service
runs fine without it (dormant-seam pattern, base repo's own design) — API-key auth works
today, owner login will need that registration whenever มอส is ready to wire up SSO.
