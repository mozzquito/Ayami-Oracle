"""Jev as claim VERIFIER (Noul 'supported' + Noul 'contradicted'). Pre-registered rule: predicted supported iff supported >= 0.65.
Usage: uv run --project ../jev-gate python run.py preflight | run --env-file <file> [--repeats 3]
Sends only public TypeSafe-docs text and gate.py code excerpts to api.typesafe.ai."""
import argparse, json, os, statistics as st, sys
from pathlib import Path
from claims import CLAIMS, ABSENCE

ROOT = Path("/Users/phongcheatphus/ayami-oracle")
SRC = {"docs": ROOT / ".tmp/typesafe-team/docs-full.txt", "gate": ROOT / "ψ/lab/jev-gate/gate.py"}
MODEL = os.environ.get("JEV_MODEL", "jev-1.13.0")
THRESH, GREY = 0.65, 0.35  # pre-registered
SUPP = ("The passage directly supports the claim exactly as stated, including any characterization, comparison or number in it, "
        "not just part of it.")
CONTRA = "The passage contradicts the claim, or shows that the claim's key assertion is false."
CHOICE_CRIT = {"supported": "The passage directly supports the claim exactly as stated, including any characterization, comparison or number in it.",
               "contradicted": "The passage contradicts the claim, or a key number, condition or characterization in the claim is different from the passage.",
               "not_addressed": "The passage does not address the claim, or supports only part of it or only the underlying facts but not its characterization."}

def passage(key, a, b):
    return "".join(SRC[key].read_text(encoding="utf-8").splitlines(keepends=True)[a - 1:b])

def preflight():
    bad = 0
    for cid, who, claim, key, (a, b), gold, must in CLAIMS:
        p = passage(key, a, b)
        miss = [m for m in must if m not in p]
        flag = "OK " if not miss else "BAD"
        bad += bool(miss)
        print(f"{flag} {cid:4} {who:8} gold={gold:13} lines {key}:{a}-{b} chars={len(p):5} " + (f"MISSING {miss}" if miss else ""))
    print("\nplanted/absence claims (no keywords) are judged by Claude's manual reading, see claims.py header")
    print("PREFLIGHT", "FAILED" if bad else "passed", f"({len(CLAIMS)} claims)")
    return bad

def run(env_file, repeats):
    for line in Path(env_file).read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip())
    from typesafe_sdk import Choice, Noul, RetryPolicy, TypeSafeClient
    c = TypeSafeClient(api_key=os.environ["TYPESAFE_API_KEY"], model=MODEL, retry=RetryPolicy(max_retries=2, timeout=40.0))
    qs = {"supported": Noul(instructions=SUPP), "contradicted": Noul(instructions=CONTRA),
          "verdict": Choice(instructions="How does the passage relate to the claim?", criteria=CHOICE_CRIT)}
    rows = []
    for cid, who, claim, key, (a, b), gold, must in CLAIMS:
        state = {"claim": claim, "passage": passage(key, a, b)}
        s, k, ch, chp = [], [], [], []
        for _ in range(repeats):
            r = c.system_one(state=state, questions=qs)
            s.append(r.nouls["supported"].noul); k.append(r.nouls["contradicted"].noul)
            a = r.choices["verdict"]; ch.append(a.choice); chp.append(a.probabilities.get("supported", 0.0))
        rows.append(dict(id=cid, who=who, gold=gold, claim=claim, supp=s, contra=k, choice=ch, p_supp=chp))
    json.dump(rows, open("results.json", "w"), ensure_ascii=False, indent=1)
    return rows

def verdict(m): return "supported" if m >= THRESH else ("unsure" if m >= GREY else "not_supported")

def report(rows):
    print(f"model={MODEL} claims={len(rows)} repeats={len(rows[0]['supp'])}  rule: supported>={THRESH}, unsure {GREY}-{THRESH}, else not_supported\n")
    print(f"{'id':4} {'src':8} {'gold':13} {'mean_supp':>9} {'range':>11} {'contra':>6}  jev_verdict   flips")
    conf = {"TP": 0, "FN": 0, "FP": 0, "TN": 0, "unsure_pos": 0, "unsure_neg": 0}
    for r in rows:
        m = st.mean(r["supp"]); v = verdict(m)
        flips = len({("sup" if x >= THRESH else "no") for x in r["supp"]}) > 1
        pos = r["gold"] == "supported"
        if v == "unsure": conf["unsure_pos" if pos else "unsure_neg"] += 1
        elif v == "supported": conf["TP" if pos else "FP"] += 1
        else: conf["FN" if pos else "TN"] += 1
        mark = "" if (v == r["gold"]) else ("   <-- DISAGREES")
        print(f"{r['id']:4} {r['who']:8} {r['gold']:13} {m:9.2f} {min(r['supp']):.2f}-{max(r['supp']):.2f} {st.mean(r['contra']):6.2f}  {v:13} {'FLIP' if flips else ''}{mark}")
    print("\nconfusion (rule pre-registered):", conf)
    n = len(rows); dec = conf["TP"] + conf["FN"] + conf["FP"] + conf["TN"]
    print(f"decided {dec}/{n}; correct among decided {conf['TP']+conf['TN']}/{dec}; false supports (dangerous) {conf['FP']}; missed supports {conf['FN']}")
    for who in ("agy", "zcode", "planted", "subtle"):
        rs = [r for r in rows if r["who"] == who]
        ok = sum(verdict(st.mean(r["supp"])) == r["gold"] for r in rs)
        print(f"  {who:8} exact agreement with Claude's manual gold: {ok}/{len(rs)}")
    # V2: Choice(supported / contradicted / not_addressed): predicted supported iff MAJORITY of repeats == "supported"
    print("\nV2 Choice variant (majority of repeats == supported):")
    tp = fn = fp = tn = 0
    for r in rows:
        maj = max(set(r["choice"]), key=r["choice"].count); pos = r["gold"] == "supported"; pred = maj == "supported"
        tp += pos and pred; fn += pos and not pred; fp += (not pos) and pred; tn += (not pos) and not pred
        if pred != pos: print(f"   V2 DISAGREES {r['id']:4} gold={r['gold']:13} majority={maj:13} choices={r['choice']} mean p(supported)={st.mean(r['p_supp']):.2f}")
    print(f"   V2 confusion: TP={tp} FN={fn} FP={fp} TN={tn}  correct {tp+tn}/{len(rows)}")
    ab = [r for r in rows if r["id"] in ABSENCE]; rest = [r for r in rows if r["id"] not in ABSENCE]
    f = lambda rs: sum(verdict(st.mean(x["supp"])) == x["gold"] for x in rs)
    print(f"V1 agreement excluding absence claims {sorted(ABSENCE)}: {f(rest)}/{len(rest)}; on absence claims only: {f(ab)}/{len(ab)}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["preflight", "run", "report"])
    ap.add_argument("--env-file"); ap.add_argument("--repeats", type=int, default=3)
    a = ap.parse_args()
    if a.cmd == "preflight": sys.exit(preflight())
    if a.cmd == "run": report(run(a.env_file, a.repeats))
    if a.cmd == "report": report(json.load(open("results.json")))
