---
pattern: "Learned OpenThai-SystemOne: 0.8B Apache-2.0 Thai/English System One clone runs locally on an 8 GB M1 (deterministic, 0.6 s) but is clearly weaker than TypeSafe Jev; upstream server can OOM"
date: 2026-09-21
source: learn: iapp-technology/openthai-systemone
concepts: ["learn", "openthai", "system-one", "jev", "local-model", "evaluation", "zcode", "agy"]
---

# Learned OpenThai-SystemOne
- Local, private, free, deterministic; TypeSafe-compatible API (SDK works with only base_url changed). But on our Thai+English intent / Score / injection / verifier tests it scored well below TypeSafe Jev
  (e.g. injection 8/12 + 2 false alarms vs 12/12 + 0; verifier 16/33 vs 29/33). Not adopted for jev-gate; kept for re-testing on the next version.
- The vendor's Thai headline numbers are in-domain (train splits of the same datasets); baselines are copied from Bespoke Labs; ECE is measured on the calibration sources.
- Upstream server loads the model lazily via lru_cache -> concurrent first requests load several ~3 GB copies -> exit 137 on 8 GB. Load once at startup and serialize requests.
- General: when a tool "times out", read the server log before retrying; verify a reviewer's specific claims against files (zcode said pickle, it was safetensors); pin revisions and check hashes before running third-party weights.
- Notes: ψ/lab/openthai-local/README.md; ψ/learn/iapp-technology/openthai-systemone/2026-09-21/0211_TEAM-EVAL.md. Related: [[2026-09-21_typesafe-docs-team-learn]].
