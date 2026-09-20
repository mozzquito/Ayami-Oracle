# jev-verifier (experiment, not used anywhere)

Tests Jev as the 4th agent in a team with Claude, /zcode and /agy: zcode and agy produced claims about the TypeSafe docs and about
gate.py; Jev judged whether a cited passage supports each claim; Claude (Ayami) held the gold labels and arbitrated. Follows the rule in
../jev-gate/README.md: Jev is never the only opinion; zcode and agy audited the gold labels and the design BEFORE the run and critiqued
the interpretation AFTER it.

Needs the docs text locally (gitignored): `mkdir -p .tmp/typesafe-team && curl -sL https://docs.typesafe.ai/llms-full.txt -o .tmp/typesafe-team/docs-full.txt`
(line numbers in claims.py refer to the copy downloaded 2026-09-21; the docs change, so re-check with `preflight`). Paths in run.py are absolute to this repo.

```bash
uv run --project ../jev-gate python run.py preflight                       # offline: every 'supported' gold has its proof text in the passage
uv run --project ../jev-gate python run.py run --env-file <file> --repeats 3   # ~100 requests, public docs text only
uv run --project ../jev-gate python run.py report
```
Rule fixed before the run: predicted supported iff mean Noul "supported" >= 0.65 (unsure 0.35-0.65). Results: ψ/learn/docs.typesafe.ai/2026-09-21/0141_TEAM-LEARN.md (section 7).
