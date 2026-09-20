# Handoff: TypeSafe Jev trial, jev-gate / jev-verifier, OpenThai-SystemOne eval

📡 Session: 2d36a871 | ayami-oracle | 2026-09-20 09:31 → 2026-09-21 03:05 (≈16h wall clock, ≈6h active)

**Date**: 2026-09-21 03:05
**Context**: ~604k tokens (limit 250k) — start a FRESH session; do not continue in this one.
**Oracle**: Ayami (หญิง, ใช้ "ฉัน") | **Human**: มอส (ชาย) | Solo | Language: Thai first

## What We Did
- Learned TypeSafe AI / Jev (docs, blog, privacy policy); tested it on the real API with synthetic Thai/English sets (easy 51/52; hard: Score 14/15, injection 12/12 + 0 FP, intent 19/23). Jev scores are NOT deterministic (about ±0.04).
- Built `ψ/lab/jev-gate` (advisory prompt-injection screen, fail-closed, 18 offline tests) and `ψ/lab/jev-verifier` (Jev as claim verifier, 29/33 vs Claude's gold; false support on a one-digit number swap, missed implicit arithmetic).
- Rule written in `ψ/lab/jev-gate/README.md`: use Jev only together with /zcode and /agy (read-only second opinions), Claude verifies every claim against source.
- Team learn of docs.typesafe.ai (agy + zcode + Grok Bot): cookbooks are vendor-run/small-n but disclose biases; the headline 193.6x/444.6x appear nowhere in the docs.
- Evaluated OpenThai-SystemOne (open 0.8B, Apache-2.0) locally on the M1 8 GB: works (0.55-0.78 s, deterministic) but clearly weaker than Jev on our tasks → NOT adopted. Upstream server OOM-killed (lazy lru_cache loads); wrote hardened `ψ/lab/openthai-local/serve.py` (6 tests).
- Installed Claude Code plugin `typesafe@typesafe-ai` 0.5.7 (user scope) at Moss's request; helped fill the TypeSafe waitlist form.
- Two retros written: `ψ/memory/retrospectives/2026-09/21/02.08_jev-team-gate-verifier.md` and `02.48_openthai-systemone-local-eval.md` (recurring pattern flagged: act/assert before verifying, 3 of last 7 metric rows).

## Git state (verify with git before acting)
- Branch `lab/jev-gate` is checked out in the SHARED main worktree and is 8 commits ahead of main; NOT pushed.
- MY commits: af04554e (jev-gate), 782ac746 (README rule), 95d15cfd (jev-verifier), f38acb7b (rrr retro), 82a2c773 (openthai-local).
- NOT mine on that branch: 98e63b17 (ZCode learn), 4829c3ce (token-check hook fix), 07929c60 (slim CLAUDE.md) — committed at 02:58 and 03:03 by OTHER Claude sessions (bab81e2d, 6653c385, 831d68ba were active in this directory).
- WARNING: several sessions share this directory and this checked-out branch. A `git switch` here changes the files under all of them, and other sessions keep committing on the branch. Use `git worktree add` for any new branch; never rebase/amend/reset this one (hash divergence, and my notes cite these hashes).
- Uncommitted (mine): ψ/memory/learnings/2026-09-21_openthai-systemone-local-eval.md, 2026-09-21_read-the-log-before-retrying-a-struggling-service.md, retro 02.48; a new row in session-metrics.md sits among ~50 uncommitted rows from other sessions (some may contain client/work details: ask Moss before touching or staging that file wholesale). ψ/learn/ is gitignored (notes there exist locally only; force-add is against Golden Rule 1).
- Outside git: auto-memory files (project_typesafe_jev_trial, project_openthai_systemone_eval, feedback_verify_before_asserting, MEMORY.md); `.tmp/openthai/` (venv 720 MB + model 1.4 GB, gitignored); ghq clone iapp-technology/openthai-systemone; `.tmp/typesafe-team/docs-full.txt`.

## Pending
- [ ] Moss: revoke the Vercel (vck_…) and TypeSafe (apikey_…) API keys that were pasted into chat (full keys remain in the session log ~/.claude/projects/-Users-phongcheatphus-ayami-oracle/2d36a871-….jsonl and a temp .env)
- [ ] Moss: confirm the 01:48 request "improve ARRA Oracle GrokBot Bridge" (repo under github.com/Soul-Brews-Studio/ — name unknown) — it never reached Claude in the conversation, so it was NOT started
- [ ] Grok Bot message c92d6e76-0e7d-433e-a8ca-75bf2d788d51 (agent "jev") still reply_pending after 70+ min — check the Grok app UI; do not resend with a new id
- [ ] Moss decides: commit the uncommitted retro/lessons (and how to treat gitignored ψ/learn)
- [ ] Moss decides: permanent API-key storage (Keychain was declined; temp files get wiped on session resume)
- [ ] Moss decides: delete .tmp/openthai (2.2 GB) or keep it for a later OpenThai re-test
- [ ] Moss decides: what to do with ~50 uncommitted metrics rows of other sessions in session-metrics.md

## Next Session (first batch — local only, no push, no delete, no amend/rebase)
- [ ] Create a NEW worktree branch from main (e.g. `git worktree add ../ayami-jev-pr -b lab/jev-pr main`) and cherry-pick af04554e 782ac746 95d15cfd 82a2c773 (not 98e63b17, 4829c3ce, 07929c60, f38acb7b); keep lab/jev-gate untouched
- [ ] gate.py: remove the AI_GATEWAY_API_KEY fallback and log 429 errors; keep thresholds, question wording and retry budget unchanged (README says ask Moss first); run the 18 tests (uv run --with pytest pytest -q)
- [ ] Write a short pre-action checklist (what did the log/source/last run actually say? before retry, before stating a fact, before quoting a number from one run) and a small RAM/swap preflight script for heavy local jobs on the M1 8 GB
- [ ] Add zsh pitfalls to auto-memory (unquoted [...] subscripts, command-in-variable word splitting, unquoted globs, function-vs-alias)
- [ ] Then, if Moss wants: numeric stress test for the jev-verifier (exact / magnitude swap / one-digit typo / implicit arithmetic, >=5 repeats)
- [ ] NOT yet: wiring jev-gate into /learn, /watch or a WebFetch hook (needs Moss + zcode + agy sign-off; shadow mode first); more OpenThai testing (agy: low value)

## Key Files
- ψ/lab/jev-gate/{gate.py,test_gate.py,live_eval.py,README.md,DESIGN.md}
- ψ/lab/jev-verifier/{claims.py,run.py,results.json,README.md}
- ψ/lab/openthai-local/{serve.py,test_serve.py,README.md,results/}
- ψ/memory/retrospectives/2026-09/21/{02.08_jev-team-gate-verifier.md,02.48_openthai-systemone-local-eval.md}
- ψ/memory/learnings/2026-09-21_*.md
- ψ/learn/docs.typesafe.ai/2026-09-21/0141_TEAM-LEARN.md and ψ/learn/iapp-technology/openthai-systemone/2026-09-21/0211_TEAM-EVAL.md (local only, gitignored)
