# jev-gate — screen external content for prompt injection before an agent reads it (DESIGN, draft 2026-09-20)

## Requirement (validated by มอส: "ลองตามคำแนะนำ")
- Before Ayami/agents read content from OUTSIDE (web pages, docs, pasted blocks, PDFs-as-text), tell me if it contains
  instructions aimed at an AI. Advisory only.
- Must-have: CLI `screen`, JSON verdict + exit code, fail-closed, no key in repo, shadow log, tests.
- Not now: Claude Code hooks, auto-blocking, Discord bot changes, anything touching PII/eVisa/email.

## Evidence from trials (synthetic, n small)
- Noul question INJ: 12/12 attacks >= 0.92, 12/12 benign <= 0.33 (incl. "ignore my previous email", role-play, Thai).
- Docs: large state full of irrelevant detail = known weak spot; 32k-token state budget; adversarial content = known weak spot.

## Design
- Python + uv, `typesafe-sdk`. Pinned model `jev-1.13.0` (env JEV_MODEL). Key from env TYPESAFE_API_KEY or --env-file. Never printed/logged.
- Input: file or stdin. Split into chunks (~6000 chars, 500 overlap), one request per chunk (same tested Noul question),
  threads for parallelism, cap 40 chunks (over cap => verdict "partial", not "clean").
- Verdict: max noul over chunks >= threshold (default 0.5) => flagged (exit 3); all < threshold => clean (exit 0);
  any API error/timeout after retry => error (exit 4). NEVER "clean" when unscreened.
- Output JSON: verdict, max_score, threshold, chunks, flagged=[{chunk, score, preview<=120 chars}], model.
- Shadow log: append-only ψ/lab/jev-gate/shadow.jsonl (ts, source label, sha256, length, max_score, verdict); NO full text; gitignored.
- Privacy: content is sent to api.typesafe.ai (retention unspecified) -> stderr notice; README: public/web content only.

## Open questions for reviewers
1. Is chunk size/overlap reasonable given the "large irrelevant state" weakness? Any better splitting?
2. Failure modes of using a classifier as an injection gate (evasion, encoding tricks, split payloads across chunks)?
3. Is fail-closed + advisory-only the right stance? What would make this dangerously give false confidence?
