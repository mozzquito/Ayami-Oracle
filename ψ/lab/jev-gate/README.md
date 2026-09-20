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

See DESIGN.md (design + reviewer questions) and ψ/learn/docs.typesafe.ai/2026-09-20/0931_OVERVIEW.md (trial results).
