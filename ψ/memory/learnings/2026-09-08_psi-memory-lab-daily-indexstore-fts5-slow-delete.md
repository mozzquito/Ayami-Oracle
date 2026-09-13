---
pattern: psi-memory's IndexStore.deleteSnapshotContent does a full FTS5 btree scan per document replace during `psi-memory index` — daily indexing can appear to hang for many minutes on a single file as the FTS5 table grows
date: 2026-09-08
source: launchd cron audit (ayami-oracle, com.ayami.psi-memory-lab-daily)
concepts: [psi-memory-lab, sqlite, fts5, launchd, cron, performance, known-issue]
status: open — not fixed, tracked as known issue
---

# `com.ayami.psi-memory-lab-daily` can stall for many minutes inside SQLite FTS5 delete — known perf issue, not a hang

## What happened

Auditing local launchd cron jobs (`com.ayami.*` in `~/Library/LaunchAgents/`) turned up
two separate failures on `com.ayami.psi-memory-lab-daily`:

1. A stale process (PID 26408) had been running for **1 day 4 hours at 0.0% CPU** —
   a genuine orphan/hang from a previous invocation that `launchctl kickstart` (without
   `-k`) silently returned instead of restarting. Fixed by `kill -9` + `kickstart -k`.
2. After a clean restart, the **new** process also appeared stuck — log progress frozen
   at "Processing 0 of 409" for 10+ minutes, 0-1% CPU. Looked identical to another hang.

## Root cause (case 2 — the real finding)

`sample <pid> 3` on the swift `psi-memory` binary showed it was NOT deadlocked — it was
doing genuine (but pathological) disk I/O:

```
IndexStore.replaceDocument
  → SQLiteConnection.withDocumentSavepoint
    → IndexStore.deleteSnapshotContent(revisionID:documentID:)
      → SQLiteConnection.execute → sqlite3_step → fts5NextMethod
        → sqlite3VdbeExec → btreeNext/moveToChild → pread (thousands of calls in a 3s sample)
```

Every time `psi-memory index` replaces one document, it deletes the document's old FTS5
content via what looks like a full btree scan rather than a targeted delete-by-rowid. As
the FTS5 table grows (10,822 chunks / 18,298 catalogued files at time of writing), each
single-document replace gets slower — trending toward O(n²) across a full indexing run.
This reads as "hung" because progress logging only fires between documents, and one
document can now take many minutes.

## How to tell the two failure modes apart

| Signal | Real hang (case 1) | FTS5 slow-delete (case 2) |
|---|---|---|
| `ps -o etime,%cpu` | 0.0% CPU, elapsed spans hours/days | 1%+ CPU, actively burning time |
| `sample <pid> 3` | Stack sits in mach_msg / idle wait | Stack deep in sqlite3 pread loop |
| Fix | `kill -9` + `launchctl kickstart -k` | Not actually fixable by restarting — same slowdown recurs as the DB grows |

`launchctl kickstart -p` (no `-k`) does NOT restart an already-running job — it just
returns the existing (possibly stale) PID. Always use `-k` to force-restart, and always
check `ps -o etime,%cpu -p <pid>` before assuming a kickstart worked.

## Status: not fixed

Options identified:
- ~~`VACUUM`/rebuild `~/Library/Application Support/PsiMemory/index.sqlite` to reduce
  FTS5 fragmentation~~ — **tried 2026-09-08, ruled out.** See below.
- Report/patch upstream `psi-memory-lab` — `IndexStore.deleteSnapshotContent` should
  delete by rowid/docid directly instead of a full FTS5 scan. **This is the only real
  fix.**
- Left running as-is for now; daily indexing is non-critical (no downstream job depends
  on same-day freshness), so the slowness is tolerated rather than blocking.

### VACUUM experiment (2026-09-08, ruled out fragmentation as the cause)

Backed up `index.sqlite` (`cp` to `index.sqlite.backup-20260908-1715`), ran
`PRAGMA integrity_check` (ok), then `VACUUM;` (53s), then `integrity_check` again (ok).

| | before | after |
|---|---|---|
| file size | 587 MB | **604 MB (grew)** |
| integrity_check | ok | ok |

VACUUM did not shrink the file — it grew slightly. This confirms the slowness is **not**
disk/page fragmentation; it's the algorithmic full-btree-scan-per-delete behavior in
`IndexStore.deleteSnapshotContent` itself. Rebuilding the file layout doesn't change how
many pages that scan has to walk each time. **Don't retry VACUUM as a fix for this — go
straight to patching the delete-by-rowid logic upstream.**

## Generalizable rule

Before killing a "stuck" background process, take a `sample <pid> 3` stack snapshot
first. A process at near-0% CPU for an abnormal `etime` is a genuine hang (safe to kill
and restart). A process burning real CPU/IO but making no visible log progress is doing
slow work, not hanging — killing and restarting it will just hit the same slowdown again;
the fix belongs in the algorithm, not in retrying the job.
