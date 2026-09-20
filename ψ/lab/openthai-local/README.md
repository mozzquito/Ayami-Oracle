# openthai-local — running OpenThai-SystemOne (0.8B, Apache-2.0) locally + evaluation against TypeSafe Jev

Evaluated 2026-09-21 on Moss's machine (Apple M1, 8 GB). **Verdict: NOT adopted** as a backend for jev-gate / jev-verifier — it is clearly
weaker than TypeSafe's Jev on our tasks. Kept: a hardened local server, the eval results, and the setup notes, so it can be re-tested when a new version appears.

## What it is
`iapp/OpenThai-SystemOne` (iApp Technology / OpenThai, v0.1, released 2026-09-20): Qwen3.5-0.8B-Base, continued-pretrained on ~5B Thai tokens,
LM head replaced by a 256-way slot head; answers Choice / Score / Noul questions in one forward pass; API contract mirrors TypeSafe `POST /v1/systemone`.
Verified from primary sources: Apache-2.0, `model.safetensors` 1,505,386,774 bytes (752,674,883 BF16 params; only safetensors, no pickle),
HF revision `e00959d170784267358928104b220348f0deaf18`, sha256 `f1893a6a005902da12282d18c8cb8e84b6f19d09bf9c20dc3ab991796b7c45ee` (matches the HF API).
The 4 custom-code files on HF (modeling/configuration/formatting/types.py) are byte-identical to the GitHub package, so we install from the reviewed
GitHub clone and never need `trust_remote_code`. Upstream unit tests: 19 passed.

## Setup (all gitignored under .tmp/; ~2.2 GB)
```bash
uv venv --python 3.12 .tmp/openthai/.venv
VIRTUAL_ENV=.tmp/openthai/.venv uv pip install "${OPENTHAI_CLONE}[server,dev]"     # clone: ghq get iapp-technology/openthai-systemone (read it first)
hf download iapp/OpenThai-SystemOne --revision e00959d170784267358928104b220348f0deaf18 --local-dir .tmp/openthai/model --exclude "assets/*"
HF_HUB_OFFLINE=1 OPENTHAI_SYSTEMONE_MODEL=$PWD/.tmp/openthai/model .tmp/openthai/.venv/bin/uvicorn serve:app --app-dir ψ/lab/openthai-local --host 127.0.0.1 --port 8765
```
Then any TypeSafe SDK code works unchanged with `TYPESAFE_BASE_URL=http://127.0.0.1:8765` (verified with typesafe-sdk 0.7; the extra `abstain` field is accepted).
Measured on the M1: load ~10-20 s, first call ~5-9 s (MPS warm-up), then 0.55-0.78 s per request (CPU 3.7 s), ~1.4-2.2 GB RSS, **deterministic** (identical to 6 decimals across repeats and across MPS/CPU).

## Why serve.py instead of the upstream server
The upstream server loads the model lazily via `lru_cache`. Concurrent first requests (or SDK retries after its default 10 s timeout) each load their own ~3 GB copy;
on this 8 GB machine that got the process killed (exit 137; the log shows the "Loading weights" bar repeating 5+ times). It also allows CORS from `*`, has no auth,
and never truncates question text (unbounded memory). `serve.py` (6 offline tests, mutation-checked): eager single load, one inference at a time, no CORS, Host must be
loopback (DNS-rebinding guard), optional bearer token, size limits (413). Not a security product; keep it on 127.0.0.1 and start it only when needed.

## Results on OUR synthetic sets (unchanged prompts and gold; TypeSafe numbers from earlier runs)
| Suite | TypeSafe Jev (remote, jev-1.13.0) | OpenThai-SystemOne 0.8B (local) |
|---|---|---|
| Easy intent, 52 msgs (Thai 24 / en 24 / mixed 4) | 51/52 (Thai 23/24) | 42/52 (Thai 19/24); Thai-worded prompts: 43/52 |
| Noul "needs reply or action" | 51/52 | 20/52 (= always "no") |
| Score urgency 0-3 (15) | 14/15 exact, MAE 0.08 | 11/15, MAE 0.47 (severe cases under-scored) |
| Injection screen (12 attacks / 12 benign) | 12/12, 0 false alarms | 8/12 caught, 2 false alarms at 0.5 (Thai wording: 7/12, 0 FP; >=0.65: 5/12) |
| Hard intent (23, incl. 7 unclear) | 19/23 | 12/23 ("command" 0/4) |
| Claim verifier, 33 claims | 29/33 (1 false support) | 16/33 exact, 6 false supports |
| Verifier on 12 claims about OpenThai itself | 9/12 (0 wrong, 3 unsure) | 4/12 |
| Latency / determinism | ~0.3-0.5 s + network / +-0.04 noise | 0.55-0.78 s (M1 MPS) / exact |
| Privacy / cost | remote, retention unspecified / $0.042 per 1M tokens | nothing leaves the machine / free |

Same direction as the vendor's own table (61.9 vs Jev 76.0 macro). Caveats: my sets and wording (written to TypeSafe's docs style), n is small, Thai-wording probe
was run after seeing the data (exploratory only), v0.1 of the model. Details and the reviewer audit: ψ/learn/iapp-technology/openthai-systemone/2026-09-21/ (gitignored) and
ψ/memory/learnings/2026-09-21_openthai-systemone-local-eval.md. Raw results: results/.

## Evidence caveats found in the vendor's material (verified against the repo)
- "Zero-shot" means no in-prompt examples; the training data does include the TRAIN splits of datasets that are also used for the public benchmarks and the Thai
  test sets (MASSIVE-th, Prachathai, XNLI-th, Wongnai) -> headline Thai numbers are in-domain results, not general ability. Not test-set leakage (train vs test/validation).
- Nimble-9B / Jev numbers are copied from Bespoke Labs' publication (MODEL_CARD.md), not measured by the OpenThai authors; ECE is measured on the same sources it was calibrated on.
- The authors admit weak spots (Thai sentiment, banking77-style fine-grained intents, extractive QA, English calibration). They do not test prompt-injection robustness.

## Possible uses / next steps (none built)
Non-critical Thai tagging where a wrong answer is cheap (after testing on real, held-out data with a dev/test split); re-test on the next release; never as the only screen or verifier.
Nothing here is wired into any hook, bot, skill or launchd job. Reminder: Jev rule in ../jev-gate/README.md (use with /zcode and /agy).

## Reproducibility notes
- `verify_openthai_claims.py` uses absolute paths to this machine (the ghq clone and a saved copy of the HF API JSON:
  `curl -sL "https://huggingface.co/api/models/iapp/OpenThai-SystemOne?blobs=true" -o hf.json`, then edit `HF_JSON`); run its `preflight` first.
- `probe_thai_prompts.py` needs the round-1/2 trial scripts (`ψ/learn/docs.typesafe.ai/2026-09-20/trial/`, gitignored, local only).
- Keys: this folder never stores any; local runs use a dummy key. The remote (TypeSafe) verifier run used a temporary key file outside the repo.
