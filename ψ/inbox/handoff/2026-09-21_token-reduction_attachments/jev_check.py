import os, sys, statistics as st
from pathlib import Path
sys.path.insert(0, "/Users/phongcheatphus/ayami-oracle/ψ/lab/jev-verifier")
import run as V   # reuse the pre-registered SUPP/CONTRA instructions and thresholds
for line in Path("/Users/phongcheatphus/ayami-oracle/.tmp/typesafe/jev.env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip())
from typesafe_sdk import Noul, RetryPolicy, TypeSafeClient
c = TypeSafeClient(api_key=os.environ["TYPESAFE_API_KEY"], model=V.MODEL, retry=RetryPolicy(max_retries=2, timeout=40.0))
passage = Path(sys.argv[1]).read_text()
# gold labels fixed BEFORE the run (Claude's reading of EVIDENCE.md)
CLAIMS = [
 ("C1", "supported", "In the measured transcripts, at most 40 lines separated the last assistant usage line from the next prompt, so a 100-line window covers every measured case."),
 ("C2", "not_supported", "A 100-line window can never miss the last assistant line, whatever the transcript looks like."),
 ("C3", "supported", "When the project dir cannot be resolved, the hard-limit branch now warns and exits instead of trying to write /ψ/inbox/handoff.log."),
 ("C4", "supported", "The hook has already produced a warning inside a real Claude Code session."),
 ("C5", "not_supported", "The change makes the hook run on every tool call."),
]
qs = {"supported": Noul(instructions=V.SUPP), "contradicted": Noul(instructions=V.CONTRA)}
print(f"model={V.MODEL} rule: supported >= {V.THRESH}, unsure {V.GREY}-{V.THRESH}, else not_supported (fixed before run)\n")
ok = 0
for cid, gold, claim in CLAIMS:
    s, k = [], []
    for _ in range(3):
        r = c.system_one(state={"claim": claim, "passage": passage}, questions=qs)
        s.append(r.nouls["supported"].noul); k.append(r.nouls["contradicted"].noul)
    m = st.mean(s); v = V.verdict(m); ok += (v == gold)
    print(f"{cid} gold={gold:13} mean_supp={m:.2f} range={min(s):.2f}-{max(s):.2f} contra={st.mean(k):.2f} jev={v:13} {'' if v==gold else '<-- DISAGREES'}")
print(f"\nagreement with Claude's gold: {ok}/{len(CLAIMS)}")
