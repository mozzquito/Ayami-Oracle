# statusline-ayami (lab, 2026-09-21)

Terminal statusline for this repo. Script: `.claude/scripts/statusline-ayami.sh`. Tests: `bash ψ/lab/statusline/test_statusline.sh`
(offline, 209 checks, runs the script under macOS `/bin/bash` 3.2). Real Claude Code stdin captured as a redacted fixture: `fixtures/live-2.1.278.json`.

Built overnight while มอส slept, on his instruction: "research fully, develop any feature you see fit, commit allowed".
Nobody validated the requirement below with him yet: **it is Ayami's reading of a one-line request, please confirm or cut in the morning.**

## What it shows

```
🤖 Sonnet 5 (high) | 💰 $1.55 session / $35.80 today / $16.57 block (3h 21m left) | 🔥 $10.10/hr ⚠️ (Moderate) | ⚡5h 62% →06:40 | 🧠 148k/150k
📁 ~/ayami-oracle on 🌿 lab/jev-gate +1 ~2 ↑1 ↓3 🌳wt 🔀#12 • 📡 a8b838ac • 04:38
🎯 statusline dev (04:22) • 🧊 9m • ⏳2 (1 stale)          <- only when there is something to say (🧊 9m = prompt cache expires in 9 min)
```

| Piece | Source | Shown when |
|---|---|---|
| model, effort, `⚡fast` | stdin `model.display_name`, `effort.level`, `fast_mode` | always (`?` if missing) |
| 💰 cost, 🔥 burn | `ccusage statusline`, **cached 30 s, refreshed in a detached process** | cache exists (first render after start has none) |
| ⚡ 5h / 7d limit | stdin `rate_limits.*` | ≥ 60 % (yellow), ≥ 85 % (red) |
| 🧠 context | stdin `context_window.current_usage` = input + cache_creation + cache_read (same formula as `token-check.sh`) | usage known. Yellow from 80 % of 150k, red from 150k (then shows `/250k`), `⛔ /forward` from 250k. `TOKEN_WARN_K` / `TOKEN_HARD_K` respected |
| 🌿 branch, `+staged ~modified ↑ahead ↓behind`, 🌳 worktree, 🔀 PR | `git status --porcelain=v2 --branch -uno` (2 s cap) + stdin | inside a git repo. Untracked files are deliberately not counted |
| 🎯 / ✅ / ⏸ focus | `ψ/inbox/focus-agent-${AGENT_ID:-main}.md` | file has a TASK |
| 🧊 cache | stdin `prompt_cache.warm`, `expires_at`, `recache_tokens_if_cold` | **countdown** `🧊 26m` once the cache is ≤ 30 min from expiry (dim; yellow ≤ 10 min; `STATUSLINE_CACHE_SHOW_MIN` changes the 30; rounded up, never `0m`), so you can send something *before* it goes cold. **`🧊 cache cold (~145k to re-cache)`** when `warm == false` or `expires_at` has passed: the next message re-writes the whole context at full price. Hidden while comfortably warm and with 0 requests |
| ⏳ pending | `fleet.py pending`, cached 60 s, detached | count > 0 (red if any is STALE) |

Removed on purpose: session duration (zcode: trivia), untracked count (slow + noisy), ccusage's own 🤖/🧠 (the live values from stdin replace them).

## Requirement (assumed) → design

- **Must:** never slow or break the prompt (old script ran `npx ccusage@latest` synchronously, 0.6-1.0 s per refresh); context gauge tied to the 150k/250k handoff rule; git detail; current focus.
- **Nice:** rate-limit, cold cache, pending agent calls.
- **Non-goals:** no writes outside `.tmp/statusline/`, no network in the render path, no change to the global `~/.claude` script.
- **Render path** = one `jq` call + one `git status` + cache reads: ~75 ms. Slow data (ccusage, fleet) is stale-while-revalidate: print the cache now, refresh in a detached process (`perl setsid`, `mkdir` lock, lock older than 90 s is dead, atomic `mv`, first line only, 25 s cap that kills the whole process group).
- **Idle ticks (`refreshInterval: 60` in `.claude/settings.json`, v2, 2026-09-21).** Claude Code re-runs the command every 60 s in addition to event-driven renders (field verified in the 2.1.278 binary: `min(1)`, seconds), so the clock and the 🧊 countdown move while you are idle. A tick that shows the same `cost.total_api_duration_ms` as the previous render has no new spend, so it does **not** re-run `npx ccusage` (state: `.tmp/statusline/lastapi.<sid>`); a missing cache is still created, and a missing/garbled marker counts as "not idle" (= refresh as before). The cheap `fleet` count still refreshes on its own 60 s TTL. Render cost stays ~75 ms.
- Every value passes through a control-character strip; every segment degrades to empty; no `set -e`; exit code is always 0.

## Enable / disable

Enabled by `statusLine` in the repo's `.claude/settings.json` (project scope, overrides the global `~/.claude/scripts/statusline.sh` only in this repo).
**Rollback:** delete the `"statusLine"` block from `.claude/settings.json` (the global script is untouched and takes over again). To keep the statusline but stop the idle re-render, delete only `"refreshInterval": 60`.
Debug: `touch .tmp/statusline/debug` dumps the last stdin to `.tmp/statusline/last.json`; remove the flag afterwards.

## Verified vs. not

Verified: the stdin schema against real JSON from Claude Code 2.1.278 (not just the docs), 150 offline checks incl. hostile input, bash 3.2, empty environment, no `jq`, concurrent refreshes, hung/failed npx, real `ccusage` end to end, live caches created by the running sessions.
**Not verified:** how it looks in มอส's terminal (Ayami cannot see the screen: check line width/wrapping and the emoji widths), `prompt_cache.warm=false` never seen live yet (only fixture-tested), `pr` and `worktree` fields never present in the captured JSON (handled if absent, tested with synthetic values).

## Consulted (2026-09-21, read-only, via `fanout.py`)

- zcode (design): keep cache + focus + ctx; cut duration; simplify git counts; gate ⏳ and limits behind thresholds; warned about Thai/emoji widths. Adopted.
- agy (shell robustness): atomic writes, no `set -e`, BSD `stat`, never sync `npx`, `--no-optional-locks`. Adopted, except its `$EPOCHSECONDS` advice: **wrong here** (macOS bash is 3.2, variable is unset), `date +%s` used.

## Gotchas found while building (worth remembering)

- bash 3.2 mangles `{a,b}` inside quotes nested in `"$( )"` (test-only issue; tests use the flat `runfx` helper).
- `alarm`+`exec` kills only the direct child: a hung `npx` left `node` holding the pipe. Fixed with a process group kill (test: "hung npx killed by the time limit").
- `find -mtime +1 -delete` garbage-collects cache files, so tests must age files by hours, not years.
- `.claude/scripts/statusline.sh` (tracked) is NOT the statusLine: it is a `UserPromptSubmit` hook (prints the `🕐 04:21 | ...` line). Left alone.

## v2 consult (2026-09-21, zcode design + agy feasibility, claims verified against source)

Adopted: 🧊 expiry countdown (real `prompt_cache.expires_at` seen in this session's stdin, seconds, ~59 min ahead), `refreshInterval` (+ idle gate above).
Deferred by มอส: per-session `AGENT_ID` for the focus file (needs the writers to know their id; until then sessions in one repo still share `focus-agent-main.md`).
Not decided: pin `ccusage`, handoff-logged glyph at ≥150k, dropping unused stdin fields, whether 📡 session id stays (handoffs/recaps quote it), line 1 width (the README sample with cost is ~140 cells; measure on มอส's terminal).
Verification scorecard: zcode mostly right (its "line 1 ≈ 60-70 cells" was ~2x too low, its idle-render billing worry was moot: local command, no API); agy: feasibility answers right, **0 of 6** "latent bugs" real (byte-slicing claim contradicted by `LC_ALL=en_US.UTF-8` on line 17 + a C-locale test; IFS claim moot). agy run #1 returned nothing because it tried to fetch a URL, which headless mode denies: tell it not to.
