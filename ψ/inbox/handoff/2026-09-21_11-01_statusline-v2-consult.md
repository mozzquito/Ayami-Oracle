# Handoff: statusline-ayami shipped, v2 consult with zcode/agy pending

📡 Session: a9ba6bad | ayami-oracle
**Date**: 2026-09-21 ~11:00
**Context**: 269k (over the 250k limit) — ended on purpose

## What We Did
- Built `.claude/scripts/statusline-ayami.sh` (3-line statusline, non-blocking ccusage cache, live ctx gauge vs 150k/250k, git detail, focus, cold prompt cache, pending fleet calls, rate limit >=60%).
- Enabled via `statusLine` in the repo's `.claude/settings.json`. Global `~/.claude/scripts/statusline.sh` untouched. Rollback: delete that block.
- 185 offline checks: `bash ψ/lab/statusline/test_statusline.sh`. Design + review trail: `ψ/lab/statusline/README.md`.
- Commits on `lab/jev-gate`: ce7ebd4d (statusline), 4cc5afca (learning). Not pushed.
- Found + fixed 2 real bugs via zcode/agy review (retry storm on failed refresh; timeout not killing grandchildren). ~1/3 of reviewer claims were wrong or moot (verify each).
- Ran out of context before consulting zcode/agy on "what else to add" (มอส asked at ~11:00).

## Pending
- [ ] มอส has not confirmed the requirement (Ayami's reading of one line) — segments may be cut or added
- [ ] Nobody has seen it on the real terminal: check line width and emoji widths; 🧊, 🌳, 🔀 never seen live
- [ ] Decide pinning `ccusage@latest` (`STATUSLINE_CCUSAGE_SPEC` exists)
- [ ] Several sessions share `AGENT_ID=main` and overwrite `focus-agent-main.md`
- [ ] Uncommitted, not mine: `ψ/inbox/focus-agent-main.md`, `ψ/inbox/handoff.log`, `ψ/memory/learnings/session-metrics.md`

## Next Session
- [ ] Run the zcode + agy consult "statusline v2: what to add" (brief below), read-only, fanout.py, verify every claim
- [ ] Try `refreshInterval` (e.g. 60 s) so the clock and 🧊 update while idle; check it stays cheap (~80 ms/render)
- [ ] Ask มอส to look at the real terminal and confirm/cut segments
- [ ] Give each session its own AGENT_ID for the focus file

Brief for the consult — candidates found so far: refreshInterval; per-session AGENT_ID; pin ccusage; show handoff-logged state when ctx>=150k; unused stdin fields (lines added/removed, prompt_cache.hit_ratio, session_name, agent.name, vim.mode, previous session id). Ask: which are worth the glanceability cost, what is missing, what to remove.

## Key Files
- .claude/scripts/statusline-ayami.sh
- .claude/settings.json (statusLine block)
- ψ/lab/statusline/README.md, test_statusline.sh, fixtures/live-2.1.278.json
- ψ/memory/learnings/2026-09-21_statusline-ayami-gotchas.md
- ψ/lab/fleet-ledger/fanout.py (parallel zcode+agy, read-only)

## Context
**Oracle**: Ayami (หญิง) | **Human**: มอส (ชาย) | **Team**: solo
