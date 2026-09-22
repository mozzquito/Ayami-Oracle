# Handoff: statusline v2 shipped (🧊 countdown + refreshInterval), pushed as lab/statusline-v2

📡 Session: 5b801d01 | ayami-oracle
**Date**: 2026-09-21 17:04 (the work ran 11:02-11:30, the session then sat idle)
**Context**: not measured (short session)

## What We Did
- `/recap` with "consult zcode/agy about statusline v2": checked the previous handoff against reality (4 unpushed commits, statusLine still enabled: matched).
- Consulted zcode (design) + agy (feasibility) in parallel, read-only, through `ψ/lab/fleet-ledger/fanout.py` (group `statusline-v2`, raw output in `.tmp/fanout/20260921-110352/`, gitignored). agy's first run was EMPTY: it tried to fetch a URL and headless mode auto-denies that. Re-ran agy alone through `fleet.py run` with "do not fetch any URL".
- Verified every claim against source: zcode mostly right (its "line 1 ≈ 60-70 cells" was ~2x too low, its idle-render billing worry moot); agy: feasibility answers right, **0 of 6** "latent bugs" real (byte-slicing claim contradicted by `LC_ALL=en_US.UTF-8` on line 17 + a C-locale test).
- มอส picked candidates 1 and 3 and skipped 2 and 4. Built:
  - 🧊 prompt-cache expiry countdown (`prompt_cache.expires_at`, seconds; shown at <= 30 min, dim, yellow <= 10 min, `STATUSLINE_CACHE_SHOW_MIN`; warm-but-past-expiry shown as cold).
  - `"refreshInterval": 60` in `.claude/settings.json` (field verified in the 2.1.278 binary) + an idle gate: same `cost.total_api_duration_ms` as the last render = no `npx ccusage` re-run (`.tmp/statusline/lastapi.<sid>`).
  - Tests 185 -> 209, mutation-checked (idle gate off -> 2 fail, countdown off -> 8 fail). README + consult notes updated.
- Commit `05b7d0e1` on `lab/jev-gate` (4 paths only). มอส looked at the real terminal: "clock ok, nothing overflows the screen" (closes the width/visual-check pending item).
- Push: a plain `git push` of `lab/jev-gate` would have published `7d40feb7` (eVisa/Wayama/internal IPs, message says "local only") to the PUBLIC origin. Asked มอส -> cherry-picked the 3 statusline commits in a temp worktree onto `origin/lab/jev-gate`, 209/209 on that clean branch, pushed as **`lab/statusline-v2` (`cc703825`)**, worktree removed. No PR opened.

## Pending
- [ ] Open a PR for `lab/statusline-v2` if มอส wants one (merge only by มอส)
- [ ] Decide pinning `ccusage` (`STATUSLINE_CCUSAGE_SPEC`; still `@latest`)
- [ ] Deferred by มอส: per-session `AGENT_ID` (visible right now: the statusline shows another session's focus from `focus-agent-main.md`), handoff-logged glyph at >=150k, dropping unused stdin fields, whether 📡 session id stays
- [ ] `lab/jev-gate` is 8 commits ahead of origin and origin is PUBLIC: `7d40feb7` (eVisa/Wayama/IPs), `cadf2ed7` (Grok Bot audit retro + 29 files), `e04c6ee5`, `ec1f5b6f` etc. are local-only. NEVER plain-push that branch without reviewing them. Its 3 statusline commits (`ce7ebd4d`, `4cc5afca`, `05b7d0e1`) now exist twice under different hashes (the pushed copies are `423c5698`, `7a481fbf`, `cc703825`).
- [ ] `fanout.py`: add "do not fetch any URL" to the agy suffix (offered to มอส, not asked for, not done)

## Next Session
- [ ] Ask มอส: open the PR for `lab/statusline-v2`? and pin `ccusage`?
- [ ] If มอส wants per-session focus: agree how a session learns its own id (`AGENT_ID` at launch), then update the writers and `statusline-ayami.sh` line ~211
- [ ] Optionally patch `fanout.py` AGY_SUFFIX (one line) and rerun its tests

## Key Files
- .claude/scripts/statusline-ayami.sh
- .claude/settings.json (statusLine block, now with refreshInterval)
- ψ/lab/statusline/README.md (segment table, idle-tick design, v2 consult scorecard), test_statusline.sh (209 checks)
- ψ/memory/learnings/2026-09-21_statusline-ayami-gotchas.md
- ψ/lab/fleet-ledger/fanout.py, fleet.py
- .tmp/fanout/20260921-110352/ (raw zcode/agy answers, gitignored)

## Context
**Oracle**: Ayami (หญิง) | **Human**: มอส (ชาย) | **Team**: solo
