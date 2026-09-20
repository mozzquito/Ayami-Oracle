"""Jev (TypeSafe, remote) and OpenThai-SystemOne (local) as verifiers of claims made about OpenThai-SystemOne by agy / zcode / Claude.
GOLD = Claude's manual check on 2026-09-21 against the cited files, fixed BEFORE any verifier call. Same question wording and rule as
../jev-verifier (supported iff Noul >= 0.65, unsure 0.35-0.65). Only public repo text is sent (to api.typesafe.ai for the remote run).

  preflight:  uv run --project ../jev-gate python verify_openthai_claims.py preflight
  remote:     set -a; . <env with TYPESAFE_API_KEY>; set +a; uv run --project ../jev-gate python verify_openthai_claims.py run --repeats 3
  local:      set -a; . eval.env; set +a; uv run --project ../jev-gate python verify_openthai_claims.py run --repeats 1
"""
import argparse
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path("/Users/phongcheatphus/ghq/github.com/iapp-technology/openthai-systemone")
HF_JSON = Path("/private/tmp/claude-501/-Users-phongcheatphus-ayami-oracle/2d36a871-47e8-4b74-8dea-dcb8b30962e4/scratchpad/openthai/hf.json")
SUPP = ("The passage directly supports the claim exactly as stated, including any characterization, comparison or number in it, "
        "not just part of it.")
CONTRA = "The passage contradicts the claim, or shows that the claim's key assertion is false."


def win(path, needle, before, after):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    i = next(n for n, l in enumerate(lines) if needle in l)
    return "\n".join(lines[max(0, i - before): i + after + 1])


def hf_files():
    d = json.load(open(HF_JSON))
    return "Files in the Hugging Face repo iapp/OpenThai-SystemOne:\n" + "\n".join(f"- {s['rfilename']}" for s in d["siblings"])


CARD = REPO / "docs/MODEL_CARD.md"
# (id, source, claim, passage function, gold, must-contain keywords proving a 'supported' passage)
CLAIMS = [
    ("O1", "agy", "The model card says the Nimble-9B and Jev benchmark numbers are as published by Bespoke Labs, while OpenThai's own numbers were measured by its authors.", lambda: win(CARD, "Nimble-9B and Jev numbers are as published", 0, 1), "supported", ("as published by Bespoke Labs", "measured")),
    ("O2", "planted", "The OpenThai authors measured the Nimble-9B and Jev numbers themselves.", lambda: win(CARD, "Nimble-9B and Jev numbers are as published", 0, 1), "not_supported", ()),
    ("O3", "agy", "The model card says all reported numbers are zero-shot, meaning the model sees only the state, the instructions and the option names and descriptions.", lambda: win(CARD, "All numbers are zero-shot", 0, 1), "supported", ("zero-shot", "option names")),
    ("O4", "planted", "The model card states that none of the benchmark training data overlaps with the evaluation data.", lambda: win(CARD, "All numbers are zero-shot", 0, 1), "not_supported", ()),
    ("O5", "zcode", "The upstream server enables CORS for any origin by default.", lambda: win(REPO / "openthai_systemone/server.py", "allow_origins=", 2, 2), "supported", ('"*"',)),
    ("O6", "planted", "The upstream server requires an API key or bearer token.", lambda: (REPO / "openthai_systemone/server.py").read_text(), "not_supported", ()),
    ("O7", "claude", "The published model weights are a single safetensors file, and no pickle or .bin checkpoint is published.", hf_files, "supported", ("model.safetensors",)),
    ("O8", "zcode", "The published model weights are stored as a Python pickle checkpoint.", hf_files, "not_supported", ()),
    ("O9", "zcode", "In formatting.py only the state is truncated to fit the token budget; the question text is not truncated.", lambda: win(REPO / "openthai_systemone/formatting.py", "def spec_to_text", 0, 12) + "\n...\n" + win(REPO / "openthai_systemone/formatting.py", "budget = min(", 3, 8), "supported", ("def spec_to_text", "state_ids")),
    ("O10", "planted", "In formatting.py the question text is also truncated to fit the token budget.", lambda: win(REPO / "openthai_systemone/formatting.py", "def spec_to_text", 0, 12) + "\n...\n" + win(REPO / "openthai_systemone/formatting.py", "budget = min(", 3, 8), "not_supported", ()),
    ("O11", "claude", "After supervised fine-tuning the authors calibrated the model in a stage that used a Brier loss and learned one temperature per question type.", lambda: win(CARD, "After SFT (12k steps)", 0, 4), "supported", ("brier_weight", "temperature")),
    ("O12", "planted", "The calibration stage learned a single global temperature shared by all question types.", lambda: win(CARD, "After SFT (12k steps)", 0, 4), "not_supported", ()),
]
ABSENCE = {"O4", "O6"}  # rest on silence of the passage


def preflight():
    bad = 0
    for cid, who, claim, fn, gold, must in CLAIMS:
        p = fn()
        miss = [m for m in must if m not in p]
        bad += bool(miss)
        print(("OK " if not miss else "BAD"), f"{cid:4} {who:8} gold={gold:13} chars={len(p):5}", f"MISSING {miss}" if miss else "")
    print("PREFLIGHT", "FAILED" if bad else "passed")
    return bad


def run(repeats):
    from typesafe_sdk import Noul, RetryPolicy, TypeSafeClient

    c = TypeSafeClient(retry=RetryPolicy(max_retries=2, timeout=60.0), timeout=60.0)
    qs = {"supported": Noul(instructions=SUPP), "contradicted": Noul(instructions=CONTRA)}
    rows = []
    for cid, who, claim, fn, gold, must in CLAIMS:
        s = [c.system_one(state={"claim": claim, "passage": fn()}, questions=qs).nouls["supported"].noul for _ in range(repeats)]
        rows.append(dict(id=cid, who=who, gold=gold, supp=s))
    return rows


def verdict(m):
    return "supported" if m >= 0.65 else ("unsure" if m >= 0.35 else "not_supported")


def report(rows):
    ok = 0
    conf = {"TP": 0, "FN": 0, "FP": 0, "TN": 0, "unsure": 0}
    for r in rows:
        m, v = st.mean(r["supp"]), None
        v = verdict(m)
        ok += v == r["gold"]
        pos = r["gold"] == "supported"
        if v == "unsure":
            conf["unsure"] += 1
        elif v == "supported":
            conf["TP" if pos else "FP"] += 1
        else:
            conf["FN" if pos else "TN"] += 1
        print(f"{r['id']:4} {r['who']:8} gold={r['gold']:13} supp={m:.2f} (spread {max(r['supp'])-min(r['supp']):.2f}) -> {v:13}{'' if v == r['gold'] else '  <-- DISAGREES'}{'  [absence claim]' if r['id'] in ABSENCE else ''}")
    print("exact agreement:", f"{ok}/{len(rows)}", "|", conf)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["preflight", "run"])
    ap.add_argument("--repeats", type=int, default=3)
    a = ap.parse_args()
    if a.cmd == "preflight":
        sys.exit(preflight())
    report(run(a.repeats))
