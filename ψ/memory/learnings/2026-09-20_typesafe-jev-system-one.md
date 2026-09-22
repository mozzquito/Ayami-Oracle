---
pattern: "Learned TypeSafe/Jev: typed calibrated decision API (Noul/Choice/Score), $0.042/Mtok, English-first, early access, privacy policy silent on retention"
date: 2026-09-20
source: learn: docs.typesafe.ai
concepts: ["learn", "typesafe", "jev", "system-one", "llm-routing", "classification"]
---

# Learned TypeSafe / Jev
- Jev = "System One" model: state + typed questions in → Noul/Choice/Score + probabilities/confidence out, no text generation.
  `POST https://api.typesafe.ai/v1/systemone`, Python `typesafe-sdk`, JS `@typesafe-ai/sdk`, Claude Code plugin `typesafe@typesafe-ai`.
- Use as a cheap gate/router in front of an LLM; keep numbers/dates in code; English best, Thai untested; pin `jev-1.13.0` not `jev-latest`.
- Don't send PII (eVisa) until retention/zero-retention is confirmed with privacy@typesafe.ai.
- Full notes: ψ/learn/docs.typesafe.ai/2026-09-20/0931_OVERVIEW.md
