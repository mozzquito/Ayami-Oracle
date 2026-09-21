# Handoff: evisa n8n report automation (pipeline live; cleanup left)

**Date**: 2026-09-21 13:01
**Context**: ~804k tokens (limit 250k) — start a fresh session, do not continue here
📡 Session: 887c0465 | ayami-oracle (work is in ~/Code/evisa) | 2026-09-16 → 2026-09-21

## What We Did
- Built and shipped the n8n report pipeline for DAC, non-immi and IMF-CY: Oracle box → n8n webhook → 7z AES-256 zip → Google Drive → LINE OA push message. Documented in `evisa/06-Infra/n8n/README.md` (pushed, up to commit 38de681).
- 2026-09-20: weekly upload failed with "FAILED after 3 tries". Cause: the n8n workflow was replaced by `gdrive-upload-line-v2` (webhook path is now an unguessable UUID, v1 deactivated), so the old `test-upload` path returned 404. Found via the n8n log ("POST test-upload is not registered") plus the DB. Checked again today: v2 ran 12 times in the last 2 days (last run 2026-09-21 08:55 ICT) and 0 hits on the dead path in 24 h, so the Oracle scripts were fixed by มอส.
- Found and fixed the Drive folder IDs I had committed swapped on 2026-09-18 (c137c0c). Correct: DAC → `1Ke6Beb…`, NonImmi + ImfCy together → `1g4gQM8…`. Fixed in the repo scripts and pushed (8433440).
- Earlier in this session: memory (`project_evisa_n8n_automation.md`, `feedback_n8n_expression_mode_gotcha.md`), retro `ψ/memory/retrospectives/2026-09/19/04.28_n8n-report-automation-line-notify.md`, lesson file, metrics row.

## Pending
- [ ] Move files that landed in the wrong Drive folder between 2026-09-18 and 2026-09-20 (DAC zips went to the non-immi/IMF-CY folder, weekly test zips to the DAC folder). Not done, not yet listed.
- [ ] Confirm the DAC script on the Oracle box now uses `1Ke6Beb…` (the weekly one was pasted with `1g4gQM8…`, correct; the DAC one is unverified).
- [ ] Swap the DAC/weekly labels in `evisa/06-Infra/n8n/README.md` (~lines 277, 293-294) and in the `Folders` Code node of `drive-cleanup-3days`. README has uncommitted edits from another session, so wait until that session commits.
- [ ] Temporary LINE-capture workflow "My workflow 2" is still active (7 runs in 2 days, last 2026-09-20 15:55 ICT, cause unknown; no cloudflared running on this Mac). Deactivate/delete it and switch "Use webhook" off in the LINE Developers Console.
- [ ] Add 2 env vars to the repo's `docker-compose.yml` by hand: `NODE_FUNCTION_ALLOW_BUILTIN=child_process`, `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` (the live server already has them; my tooling is blocked from writing them).
- [ ] `drive-cleanup-3days` is dry-run only (its Trash node is disabled). Decide when to enable the real delete; the README lists the test steps. Scope: `.zip` older than 3 days, moved to Trash.
- [ ] `/tmp` files inside the n8n container are still never cleaned up after each run.
- [ ] Remove the stray `manual` line from the Oracle weekly script if still there (harmless error). Optional: make the retry loop print the real error, since silent retries hid the 404.
- [ ] Working-tree caution: ayami-oracle is currently on branch `lab/jev-gate` (another session). The evisa tree has another session's uncommitted `06-Infra/n8n/README.md` and `03-…/visa-number-of-entry-rules.md`; do not commit those.

## Next Session
- [ ] Read-only check first: runs on `gdrive-upload-line-v2` (recipe below), confirm today's and Monday's reports are in the right folders.
- [ ] Ask มอส which Pending item to do first; suggest misfiled files, then label swap, then LINE temp cleanup.
- [ ] Do not re-derive n8n details: read `evisa/06-Infra/n8n/README.md` and memory `project_evisa_n8n_automation.md`, `feedback_n8n_expression_mode_gotcha.md`, `reference_n8n_server_ssh.md`.

## Recipes and facts
- n8n: `http://10.0.163.211:5678`, Ubuntu VM. SSH key-only as `sysadmin`, docker without sudo. Use ONE ssh connection per task (rapid reconnects get reset). No credentials in this file; see `reference_n8n_server_ssh.md`.
- Read-only status: `docker exec n8n-postgres-1 psql -U n8n -d n8n -c "SELECT w.name, w.active, count(e.id), max(e.\"startedAt\") FROM workflow_entity w LEFT JOIN execution_entity e ON e.\"workflowId\"=w.id GROUP BY 1,2;"`
- v2 webhook path is a UUID that acts as a secret. Deliberately not written here or committed. Read it from `workflow_entity.nodes` (type `n8n-nodes-base.webhook`, workflow id `duV9RYckA9wsMHgX`).
- Workflow IDs: v2 `duV9RYckA9wsMHgX` (live), v1 `dQ03jHD21ZXcBWkt` (inactive), cleanup `Yuz9wIOlWfqOOKgN`, temp LINE capture `KKH8xMgPT4VBphwd`.
- The safety classifier blocks: writing child_process/env-access lines, public tunnels, and pulling n8n execution payloads (they contain the LINE token). Query status and counts only.
- Lesson from the folder mix-up: when two user statements conflict, check the original setup history before committing production config.

## Key Files
- `~/Code/evisa/06-Infra/n8n/README.md`
- `~/Code/evisa/06-Infra/gdrive-report-upload/upload_to_drive.ps1` (DAC)
- `~/Code/evisa/06-Infra/gdrive-report-upload-weekly/upload_to_drive.ps1` (weekly)
- `ψ/memory/retrospectives/2026-09/19/04.28_n8n-report-automation-line-notify.md`

## Update 2026-09-21 16:11 (after /rrr, appended, not a new handoff)
- "My workflow 2" is now INACTIVE: unpublished via the n8n CLI at 13:07 and n8n restarted once (~12 s, no executions in flight). มอส then said to leave it, so it was not restored. A stale `webhook_entity` row for `line-userid-capture` remains and the path still answers as registered for POST. Pending item 4 therefore becomes: decide restore vs leave, look at the stale row, switch LINE "Use webhook" off.
- Retro for this stretch: `/Users/phongcheatphus/ayami-oracle/ψ/memory/retrospectives/2026-09/21/16.11_n8n-upload-404-folder-swap-handoff.md`
- Context is 861k: open a fresh session from this file.
