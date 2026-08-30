---
installer: arra-oracle-skills-cli v26.5.16
origin: Nat Weerawan's brain, digitized — how one human works with AI, captured as code — Soul Brews Studio
name: inbox
description: '[lab] v26.5.16 G-SKLL | Read and write to Oracle inbox — notes, tasks, messages, handoffs. Use when user says "inbox", "leave a note", "write to inbox", "check inbox", "what''s pending", or wants to read/write messages for self or other agents. Do NOT trigger for session handoffs (use /forward), schedule (use /schedule), or agent messaging (use /talk-to).'
argument-hint: "[read | write <topic> | ls | clean]"
---

# /inbox - Oracle Inbox

Read and write timestamped notes to `ψ/inbox/`.

## Usage

```
/inbox                    # List recent inbox items
/inbox read               # List recent inbox items (alias)
/inbox read <topic>       # Read specific item by topic keyword
/inbox write <topic>      # Write new inbox item
/inbox ls                 # List all items (full)
/inbox clean              # Archive old items (move to ψ/archive/inbox/)
```

## Directory

```
ψ/inbox/
├── handoff/              # Session handoffs (managed by /forward)
├── schedule.md           # Schedule (managed by /schedule)
├── YYYY-MM-DD_HHMM_<topic>.md   # ← inbox items live here
└── ...
```

## Filename Format

Every inbox item follows this pattern:

```
YYYYMMDD_HHMM_[P0_|P1_|P2_]<topic-slug>_from_<sender>.md
```

Examples:
- `20260323_2112_fix-auth-bug_from_peter.md` (no tag = normal priority)
- `20260827_0920_P0_server-down-restart-cron_from_moss.md` (urgent)

**Rules**:
- Date: compact `YYYYMMDD` (no dashes)
- Priority tag: optional, one of `P0` (urgent — needs eyes today), `P1` (soon), `P2` (whenever). Untagged items are treated as normal priority (same bucket as `P2`) for sorting.
- Topic slug: lowercase, hyphens, no spaces
- Sender: who wrote it (oracle name or human name)
- Timestamp: local time (from `date`)
- Always at root of `ψ/inbox/` (not in subdirectories)

---

## Mode 1: Read (default)

### `/inbox` or `/inbox read`

```bash
ROOT="$(pwd)"
INBOX="$ROOT/ψ/inbox"
```

List all `.md` files in `ψ/inbox/` (excluding `schedule.md` and `handoff/`), **sorted by priority tag first (P0 → P1 → P2/untagged), most recent within each bucket**:

```bash
{
  ls -1t "$INBOX"/*_P0_*.md 2>/dev/null
  ls -1t "$INBOX"/*_P1_*.md 2>/dev/null
  ls -1t "$INBOX"/*.md 2>/dev/null | grep -v schedule.md | grep -vE '_(P0|P1)_'
} | head -10
```

`$INBOX` is absolute (set as `$ROOT/ψ/inbox` in Mode 1 Step 0), so `ls` already prints absolute paths — clickable as-is.

For each file, show (priority badge only when tagged):
```
🔴 P0 · 20260827 09:20 — server-down-restart-cron (from moss)
📥 20260323 21:12 — fix-auth-bug (from peter)
   First 2 lines of content...
```

If MCP available, also run:
```
oracle_inbox(limit=10)
```

### `/inbox read <topic>`

Find and display the most recent file matching the topic:

```bash
ls -1t "$INBOX"/*<topic>*.md 2>/dev/null | head -1
```

Read and display full content.

---

## Mode 2: Write

### `/inbox write <topic>` (optionally `/inbox write P0 <topic>` etc.)

If the topic's first word is *exactly* `P0`, `P1`, or `P2` (followed by a space or end-of-input — not immediately followed by another letter/digit), treat it as the priority tag and strip that word from the topic. Otherwise leave the tag empty (untagged = normal priority). This distinction matters: `P2P notes` or `p0rn-blocker-config` do NOT have a priority tag — `P2`/`P0` there is a prefix of a longer word, not a standalone tag.

```
/inbox write P0 server is down       → tag=P0, topic="server is down"
/inbox write p2p integration notes   → tag=(none), topic="p2p integration notes"
/inbox write P1   migration plan     → tag=P1, topic="migration plan"
```

```bash
TS=$(date +%Y%m%d_%H%M)
PRIO=""   # set to P0/P1/P2 if the user specified one (already stripped from topic below), else leave blank
SLUG=$(echo "<topic-with-tag-already-stripped>" | tr ' ' '-' | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]//g')
FROM=$(echo "<sender>" | tr ' ' '-' | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]//g')
# ${PRIO:+${PRIO}_} expands to "P0_" (etc.) when PRIO is set, or to nothing when PRIO="" —
# do NOT simplify to "${PRIO}_", that produces a stray double-underscore when untagged.
FILE="$INBOX/${TS}_${PRIO:+${PRIO}_}${SLUG}_from_${FROM}.md"
```

**Ask the user**: "What do you want to note?" (unless content is provided after topic). Only ask about priority if it isn't obvious from context — don't force a P0/P1/P2 choice on every write; untagged is the normal, expected case.

Write the file:

```markdown
---
topic: <topic>
from: <current-oracle-name>
timestamp: YYYY-MM-DD HH:MM
---

<user's content>
```

If MCP available, also call:
```
oracle_handoff(content, slug)
```

This syncs to vault for cross-Oracle discovery.

### Confirm write (announce-mode — absolute paths required)

# announce-mode → absolute path (no ψ/, no ~/, no $VAR, no ...).
# Use:  echo "marker: $RESOLVED_PATH"  — bash substitutes. See CONVENTIONS.md.

```bash
echo "📥 Written: $FILE"
```

---

## Mode 3: List All

### `/inbox ls`

Same as read but show ALL items (no limit), with file sizes, same P0 → P1 → P2/untagged ordering:

```bash
{
  ls -lht "$INBOX"/*_P0_*.md 2>/dev/null | grep -v schedule.md
  ls -lht "$INBOX"/*_P1_*.md 2>/dev/null | grep -v schedule.md
  ls -lht "$INBOX"/*.md 2>/dev/null | grep -v schedule.md | grep -vE '_(P0|P1)_'
}
```

Also count handoffs:
```bash
echo "📁 Handoffs: $(ls "$INBOX/handoff/" 2>/dev/null | wc -l) files"
```

---

## Mode 4: Clean

### `/inbox clean`

Move items older than 7 days to archive:

```bash
ARCHIVE="$ROOT/ψ/archive/inbox"
mkdir -p "$ARCHIVE"
find "$INBOX" -maxdepth 1 -name "*.md" -not -name "schedule.md" -mtime +7 -exec mv {} "$ARCHIVE/" \;
```

Report what was moved. Never delete — move to archive (Nothing is Deleted).

---

## Who Can Write?

Any Oracle, any skill, any agent. The only rule: **timestamp before topic** in filename.

| Writer | How | Example |
|--------|-----|---------|
| `/inbox write` | This skill | `20260323_2112_idea_from_neo.md` |
| `/forward` | Handoff | `ψ/inbox/handoff/20260323_2112_session-forward.md` |
| Another Oracle | `/talk-to` + write | `20260323_2112_status-update_from_odin.md` |
| Agent directly | `oracle_handoff()` MCP | Same format |

---

ARGUMENTS: $ARGUMENTS
