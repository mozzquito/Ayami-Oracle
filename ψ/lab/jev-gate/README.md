# jev-gate (prototype, advisory only)

Screens text from OUTSIDE (web pages, docs, pasted blocks) for instructions aimed at an AI, using TypeSafe's Jev (`jev-1.13.0`).
Not wired into any hook, bot, or agent. Nothing is blocked automatically. "no_instructions_detected" does NOT mean safe.

```bash
uv run python gate.py screen page.txt --send-external --env-file /path/to/.env   # or: ... screen - < text
uv run --with pytest pytest -q                                                    # offline tests, no key needed
uv run python live_eval.py --env-file /path/to/.env                               # live synthetic eval (~100 requests)
```

| exit | verdict | meaning |
|---|---|---|
| 0 | no_instructions_detected | everything scored below 0.35, no code signals |
| 2 | review | score 0.35-0.65, or invisible chars / base64-like blob seen -> a human should look |
| 3 | flagged | a chunk scored >= 0.65 |
| 4 | unscored | API error, truncated (>40 chunks / >200k chars), or refused -> UNKNOWN, never OK |

Rules of use
- `--send-external` is required every run: text goes to api.typesafe.ai (retention unspecified). Public/web content only —
  never PII, eVisa, email, secrets.
- Key comes from env `TYPESAFE_API_KEY` or `--env-file`; never stored in this repo. `shadow.jsonl` (gitignored) keeps
  hash + length + verdict only, no full text.
- Scores are NOT deterministic (±0.03-0.04 on identical input). Thresholds were set post-hoc on ~30 synthetic cases.
- Code does what code can: invisible/bidi chars stripped, NFKC applied, base64-like blobs flagged as a signal.

## Required: use Jev together with /zcode and /agy

Jev is one narrow, non-deterministic, vendor-tuned voice. It is never the only opinion behind a decision that matters.
Ayami (Claude) drives; `/zcode` (GLM) and `/agy` (Gemini / Claude Sonnet) give independent second opinions.

Ask BOTH of them (read-only) before you:
- change thresholds/bands, the Noul question wording, or the pinned model;
- wire jev-gate into any hook, skill, bot, or workflow;
- act on, or dismiss, a `flagged` / `review` result;
- use Jev for anything beyond screening (routing, verifying, scoring) or change how trial results are read.

```bash
zcode -p "<task + file paths>" --cwd "/Users/phongcheatphus/ayami-oracle" --disallowedTools "Edit Write"   # background: use `node .../zcode.cjs`, not the alias
agy   -p "<task + file paths>" --mode plan [--model gemini-3.1-pro-high]
```

How to work together
1. Split by scope (different files/questions per agent), not the same question three times; different model families on purpose.
2. Read-only for reviewers. Ayami writes the change; zcode/agy never edit this repo.
3. Ayami verifies every reviewer claim against the source lines/output before it goes into a note or a commit — reviewers over-claim
   (2026-09-21: agy called disclosed benchmark limits "deceptive"; zcode wrongly said error types were hidden; both caught only by re-checking).
4. Disagreement resolves toward caution: if Jev says nothing found but zcode/agy see a risk, treat it as `review`. Never vote a
   `flagged` result down to "safe"; a human decides.
5. The data rule covers all three: zcode and agy also send prompts to third-party models — public / non-sensitive content only.

See DESIGN.md (design + reviewer questions), ψ/learn/docs.typesafe.ai/2026-09-20/0931_OVERVIEW.md (trial results) and
ψ/learn/docs.typesafe.ai/2026-09-21/0141_TEAM-LEARN.md (team review of the docs + gate.py).
