# CLAUDE_legacy.md — inherited Nat's Agents template sections

> Moved **verbatim** out of `CLAUDE.md` on 2026-09-21 to shrink what loads every turn (Nothing is Deleted — nothing was removed, only relocated).
> **Not auto-loaded.** Read it only when you need MAW multi-agent sync, the spinoff-repo list, or the old spec-kit notes.
> Paths and references below (`/Users/nat/...`, `CLAUDE_safety.md`, etc.) are from the original template and may be stale for this repo.

---

<!-- moved from CLAUDE.md lines 40-77: Nat's Agents header, migration notice, Navigation table (links to files that do not exist) -->

# Nat's Agents - AI Assistant Quick Reference

> ⚠️ **MIGRATION IN PROGRESS** (Issue #57)
>
> This CLAUDE.md is being restructured to ultra-lean format (~500 tokens).
> Details moving to `.claude/commands/*.md` (lazy loaded).
>
> **Current phase**: Probation/Testing
> - Observe current patterns, don't assume old structure
> - Report issues/friction in retrospectives
> - Consolidate learnings after testing period
>
> **Reference**: https://github.com/laris-co/Nat-s-Agents/issues/57

> **Modular Documentation**: This is the lean hub. For details, see the linked files below.

## Navigation

| File | Content |
|------|---------|
| [CLAUDE_safety.md](CLAUDE_safety.md) | Critical safety rules, PR workflow, git operations |
| [CLAUDE_workflows.md](CLAUDE_workflows.md) | Short codes (rrr, gogogo), context management |
| [CLAUDE_subagents.md](CLAUDE_subagents.md) | All subagent documentation |
| [CLAUDE_lessons.md](CLAUDE_lessons.md) | Lessons learned, patterns, anti-patterns |
| [CLAUDE_templates.md](CLAUDE_templates.md) | Retrospective template, commit format, issue templates |

### When to Read

| File | When to Read | Priority |
|------|--------------|----------|
| `CLAUDE.md` | **Every session start** | 🔴 Required |
| `CLAUDE_safety.md` | **Before any git/file operation** | 🔴 Required |
| `CLAUDE_subagents.md` | Before spawning agents | 🟡 As needed |
| `CLAUDE_workflows.md` | When using short codes (rrr) | 🟡 As needed |
| `CLAUDE_lessons.md` | When stuck or making decisions | 🟢 Reference |
| `CLAUDE_templates.md` | When creating retrospectives/issues | 🟢 Reference |

---

<!-- moved from CLAUDE.md lines 97-167: Multi-Agent Sync (MAW) + Search in Worktrees (Nat's paths) -->

## Multi-Agent Sync (IMPORTANT!)

**Use MAW commands, not raw tmux!**

```bash
source .agents/maw.env.sh  # Always source first
maw peek                   # Check all agents
maw sync                   # Sync all to main
maw hey 1 "task"          # Send task to agent 1
```

### The Sync Pattern (FIXED)
```bash
ROOT="/Users/nat/Code/github.com/laris-co/Nat-s-Agents"

# 0. FETCH ORIGIN FIRST (prevents push rejection!)
git -C "$ROOT" fetch origin
git -C "$ROOT" rebase origin/main

# 1. Commit your work (local)
git add -A && git commit -m "my work"

# 2. Main rebases onto agent
git -C "$ROOT" rebase agents/N

# 3. Push IMMEDIATELY (before syncing others)
git -C "$ROOT" push origin main

# 4. Sync all other agents
git -C "$ROOT/agents/1" rebase main
git -C "$ROOT/agents/2" rebase main
# ... etc (or use: maw sync)
```

### Key Principles
| Rule | Why |
|------|-----|
| `source .agents/maw.env.sh` | Enable maw commands |
| Fetch origin first | Prevents non-fast-forward push rejection |
| Push before sync | Commit to remote before changing other agents |
| `git -C` not `cd` | Respect boundaries, no shell state pollution |
| `maw` not `tmux` | Use proper CLI, not raw tmux |

**See**: `/maw-boot` command for full workflow

### Search in Worktrees

**Each agent searches only its own worktree.**

| Agent | Search Path |
|-------|-------------|
| main | `/Users/nat/.../Nat-s-Agents/` (exclude `agents/`) |
| agent 1 | `/Users/nat/.../Nat-s-Agents/agents/1/` |
| agent 2 | `/Users/nat/.../Nat-s-Agents/agents/2/` |

**Detection**: Use `git -C` to check any worktree.

```bash
# Check worktree root (no cd!)
git -C /path/to/worktree rev-parse --show-toplevel

# Main must exclude agents/
find /path/to/main -name "*pattern*" -not -path "*/agents/*"

# Agents search their own root only
find /path/to/agents/N -name "*pattern*"
```

**Why**: Prevents seeing other agents' files. All synced via `maw sync`.

---

<!-- moved from CLAUDE.md lines 375-387: Spinoff Repos (oracle-status-tray) -->

## Spinoff Repos

| Repo | Purpose | Status |
|------|---------|--------|
| [oracle-status-tray](https://github.com/laris-co/oracle-status-tray) | Oracle Pulse - menu bar tray app | v0.4.0 |

### Oracle Pulse (oracle-status-tray)
- **Tech**: Tauri 2.0 + Rust + HTML/JS
- **Features**: Status dashboard, logs viewer, voice notifications via MQTT
- **Build**: `cargo tauri build` → DMG in `target/release/bundle/`
- **Dev**: `cargo tauri dev` (note: LSUIElement doesn't apply in dev mode)

---

<!-- moved from CLAUDE.md lines 415-434: Template version footer, Active Technologies, Recent Changes (spec-kit features) -->

**Last Updated**: 2025-12-28
**Version**: 5.2.0 (Migration to ultra-lean in progress)

## Active Technologies
- TypeScript 5.7 (ES2022 target) + @modelcontextprotocol/sdk, better-sqlite3, chromadb (001-oracle-mcp)
- SQLite (FTS5 for keyword search) + ChromaDB (vector embeddings) (001-oracle-mcp)
- TypeScript 5.7 (ES2022 target) + @modelcontextprotocol/sdk ^0.5.0, better-sqlite3 ^11.7.0, chromadb ^1.9.2 (002-hybrid-vector-search)
- SQLite (FTS5 for keywords) + ChromaDB (vector embeddings) (002-hybrid-vector-search)
- SQLite (FTS5 for metadata) + ChromaDB (vector embeddings - not needed for list) (047-oracle-list)
- TypeScript 5.x (Bun runtime) + Bun built-ins (bun:sqlite), Commander.js for CLI parsing (057-session-timer)
- SQLite (via bun:sqlite) - single file, portable, no server needed (057-session-timer)
- TypeScript 5.x with Bun runtime + Commander.js (CLI), Drizzle ORM (database) (061-habit-tracker)
- SQLite via bun:sqlite (local file, append-only) (061-habit-tracker)
- TypeScript 5.x (Bun runtime) + Commander.js (CLI), Drizzle ORM, bun:sqlite (064-snippet-manager)
- SQLite with FTS5 for full-text search (064-snippet-manager)

## Recent Changes
- 001-oracle-mcp: Added TypeScript 5.7 (ES2022 target) + @modelcontextprotocol/sdk, better-sqlite3, chromadb

---
