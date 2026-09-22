---
name: triage
description: 'Scan ψ/inbox/ for dumped items and route each to its correct home in ψ/ — the "put it anywhere, sort it later" half of the KOS. Use when user says "triage", "จัดหมวด inbox", "sort inbox", "clean up inbox", or wants ψ/inbox/ items filed to where they actually belong. Do NOT trigger for age-based archiving of old items (use /inbox clean) or for capturing a NEW note at write-time (use /inbox write or /fyi).'
argument-hint: "[dry-run (default) | apply]"
---

# /triage — Oracle Inbox Triage

> Dump anything into ψ/inbox/ without deciding where it goes. /triage decides later, so you don't have to decide now.

This is the missing half of `/inbox`: `/inbox write` gets things IN. `/triage` gets them to their real home.

## Step 0: Timestamp (REQUIRED)

```bash
date "+🕐 START: %H:%M:%S (%s)"
ROOT="$(git rev-parse --show-toplevel)"
```

---

## Scope — whitelist, not blacklist

Only these are triageable:

```bash
find "$ROOT/ψ/inbox" -maxdepth 1 -name "*.md" -type f \
  ! -name "focus-agent-*.md" \
  ! -name "schedule.md"
```

Everything else in `ψ/inbox/` (the `handoff/` subdir, any future live-state file that doesn't match this whitelist) is **not** triage's business — it stays untouched. This is deliberately a whitelist (only markdown files directly at inbox root, matching none of the exclusions) rather than a blacklist, so a new kind of state file added later doesn't accidentally get swept up.

---

## Step 1: Read and classify each item

Read every file in scope. For each, decide ONE primary category using the tree below, then check for a secondary category (see Precedence).

### Destination map

| Category | Destination | Filename | Index? |
|---|---|---|---|
| **task** — the note's whole point is an action item, a standalone checklist, a "don't forget to X" | *(no canonical home yet — see below)* | — | no |
| **learning** — a pattern, lesson, or decision worth remembering long-term | `ψ/memory/learnings/` | `YYYY-MM-DD_slug.md` (match existing files' naming) | no |
| **project-note** — an update/finding tied to an active project or experiment | `ψ/lab/<project>/` (use existing project subfolder if one exists under `ψ/lab/`; otherwise `ψ/lab/` root) | keep original slug | no |
| **writing-draft** — a chunk of prose meant to become an article/post | `ψ/writing/` | keep original slug | no |
| **idea** — a concept/possibility, not yet explored, not yet a decision | `ψ/lab/concepts/` | `NNN-slug.md` (next number after the highest existing `NNN-*.md`; start at `001` if the folder doesn't exist yet) | yes — `ψ/lab/concepts/INDEX.md` |
| **info** — a standalone fact or reference, not tied to a project | `ψ/memory/logs/info/` | `YYYY-MM-DD_HH-MM_slug.md` | yes — `ψ/memory/logs/info/INDEX.md` |
| **feeling** — a mood/energy entry | `ψ/memory/logs/feelings/` | `YYYY-MM-DD_HH-MM_slug.md` | yes — `ψ/memory/logs/feelings/INDEX.md` |

**No home for "task" yet.** `ψ/` has no backlog pillar today — one agent file (`marie-kondo`) references a `ψ/later/` folder, but nothing ever created it and no other skill uses it. Don't resurrect an orphaned, never-adopted decision as a side effect of this skill. A pure task item stays in `ψ/inbox/`, untouched, and is called out in the report so the human decides.

### Precedence (when an item matches more than one category)

```
task (primary intent only) > learning > project-note > writing-draft > idea > info > feeling
```

- **"task" only wins if the action item IS the note**, not if a checklist line is incidental to a longer note. A project log that ends with `- [ ] verify on prod` is still a **project-note** — classify by what the note is *about*, not by the presence of a checkbox.
- `learning` outranks `idea`: a learning is a verified/settled insight, an idea is still speculative. Don't let a speculative framing bury a settled one.
- If a note has a secondary category worth surfacing (e.g. it's mostly a task but also contains a real learning), route by primary category as above, but **mention the secondary angle in the dry-run report** so it isn't silently lost just because the file itself didn't move.
- Genuinely can't tell? Leave it in `ψ/inbox/`, flagged with why in the report. Don't guess a destination you're not confident in — a wrong guess is worse than a delay.

---

## Step 2: Build the move plan, show it, get ONE confirmation

Build a table:

```
📋 Triage plan — N items

  ไฟล์                                  →  ปลายทาง                              เหตุผล
  ────────────────────────────────────────────────────────────────────────────
  20260819_agoda-sharing.md            →  ψ/memory/learnings/2026-08-19_...    learning: pattern worth keeping
  gmail-cleanup-phongcheat-phus.md     →  (ค้างใน inbox)                        task: action item, ยังไม่มีบ้าน

  ยืนยันย้ายทั้งหมดตามนี้? (y/n)
```

- **One confirmation for the whole batch**, not per item — that's the entire point (decision fatigue is the problem this skill solves). But every row must show *why*, so the human is mirroring the decision, not rubber-stamping a black box.
- Items staying in `ψ/inbox/` (task / ambiguous) are still listed in the plan — visibility matters even when nothing moves.
- If the user says no, stop. Nothing has been touched yet — Step 2 is pure planning.

---

## Step 3: Execute via the script

Only after explicit "yes." For each item that IS moving, build one JSON line:

```json
{"src":"ψ/inbox/foo.md","dst":"ψ/memory/learnings/2026-08-19_foo.md","index_file":null,"index_row":null}
```

For categories with an INDEX.md (idea/info/feeling), include `index_file` and a pre-built `index_row` — a single markdown table row matching that INDEX's existing column format (see `note-taker` agent's format for idea/info/feeling if the INDEX doesn't exist yet — create it fresh in that shape). **Escape any `|` in the title/summary as `\|` before building the row** — the script does not touch table syntax, that's the caller's job.

Pipe all lines to the script in one batch:

```bash
cat <<'EOF' | bash "$ROOT/.claude/skills/triage/scripts/apply-moves.sh"
{"src":"...","dst":"...","index_file":null,"index_row":null}
{"src":"...","dst":"...","index_file":"ψ/lab/concepts/INDEX.md","index_row":"| 003 | 2026-08-27 | triage-skill | ... | 💡 idea |"}
EOF
```

The script does ONLY mechanical work (mkdir -p, INDEX.md update, `git mv`/`mv`+`git add`) — no judgment calls live there. It updates the INDEX before moving the file (deliberate ordering — see the script's header comment) and never aborts the whole batch on one item's failure. It returns one JSON-Lines result per input line.

---

## Step 4: Report

Read back the script's JSON-Lines output and summarize in Thai:

```
✅ ย้ายแล้ว 4 รายการ
  📚 ψ/memory/learnings/2026-08-19_agoda-claude-code-sharing.md
  💡 ψ/lab/concepts/003-triage-skill.md (+ INDEX.md)
  ...

⏸️ ค้างใน inbox 1 รายการ (ยังไม่มีบ้าน)
  📥 gmail-cleanup-phongcheat-phus.md — task, ไม่มี canonical home สำหรับ backlog ตอนนี้

❌ ล้มเหลว 0 รายการ
```

If any item's status was `"error"`, show the error and leave that file exactly where the script left it — don't retry silently.

---

## Rules

1. **Nothing is Deleted** — every move is `git mv`/`mv`, never `rm`. Reversible via `git checkout`/`git mv` back, or plain `mv` back for untracked files.
2. **Mirror, don't command** — one visible plan, one confirmation, always with reasons shown. Never auto-file without the user seeing the plan first.
3. **Whitelist scope** — only markdown files at `ψ/inbox/` root, minus the two named exclusions. Never touch `handoff/`.
4. **No canonical home for tasks yet** — don't invent one (don't resurrect `ψ/later/`) as a side effect of running this skill. If the user wants a backlog pillar, that's a separate decision.
5. **Not safe for concurrent runs** — single-user repo, no locking on INDEX.md. Fine as-is.
6. **Idempotent by construction** — an item that already left `ψ/inbox/` can't be picked up again; presence in the whitelist scan IS "still pending." No separate state file needed.
7. **Some destinations are intentionally gitignored** — `ψ/memory/logs/` (feeling, info) is ephemeral by existing repo convention (`ψ/.gitignore`), unlike `ψ/inbox/` items which are meant to be git-tracked. Moving a tracked item there is expected to make it leave git's index — the physical file is still preserved (Nothing is Deleted holds at the filesystem level), it just stops being version-controlled going forward. `apply-moves.sh` handles this automatically (`mv` + `git rm --cached` instead of `git mv`); don't treat it as an error.

---

ARGUMENTS: $ARGUMENTS
