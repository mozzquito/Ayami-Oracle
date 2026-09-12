#!/usr/bin/env python3
"""Compare repeated roasts logged by the ReonAI Roast POC firmware.

This exists to run the exact test zcode recommended before building anything
to sell: roast the same profile 20-30 times, and check whether the batches
are actually more consistent / more repeatable than a skilled manual roast —
not whether the electronics work.

Usage:
    python3 compare_roasts.py logs/*.csv
    python3 compare_roasts.py logs/*.csv --agtron agtron.csv

Each roast CSV is downloaded from the dashboard's log list (columns:
elapsed_ms,dt_c,ht_c,ror_c_per_min,ssr_duty_pct,mode,bean_type,roast_level,
setpoint_c — the last three are session metadata, repeated on every row;
older logs without them still load fine, just without that grouping info).

--agtron optionally points at a CSV with columns: file,agtron (manual color
read per roast, e.g. from a handheld Agtron/color meter or a roaster's own
scale) to correlate curve consistency with the actual outcome that matters —
color/degree of roast — not just whether the graphs look similar.
"""
import argparse
import csv
import statistics
import sys
from pathlib import Path


def load_roast(path: Path):
    rows = []
    meta = {"bean_type": "", "roast_level": "", "setpoint_c": None}
    with path.open() as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "t": float(r["elapsed_ms"]) / 1000.0,
                "dt": float(r["dt_c"]),
                "ht": float(r["ht_c"]),
                "ror": float(r["ror_c_per_min"]),
            })
            # session metadata is repeated on every row; grab it once
            if not meta["bean_type"] and r.get("bean_type"):
                meta["bean_type"] = r["bean_type"]
            if not meta["roast_level"] and r.get("roast_level"):
                meta["roast_level"] = r["roast_level"]
            if meta["setpoint_c"] is None and r.get("setpoint_c"):
                try:
                    meta["setpoint_c"] = float(r["setpoint_c"])
                except ValueError:
                    pass
    return rows, meta


def time_to_temp(rows, target_c):
    """Seconds elapsed until DT first reaches target_c, or None if never."""
    for r in rows:
        if r["dt"] >= target_c:
            return r["t"]
    return None


def summarize(name, rows, meta):
    dts = [r["dt"] for r in rows]
    rors = [r["ror"] for r in rows]
    return {
        "name": name,
        "bean_type": meta.get("bean_type", ""),
        "roast_level": meta.get("roast_level", ""),
        "setpoint_c": meta.get("setpoint_c"),
        "duration_s": rows[-1]["t"] if rows else 0,
        "max_dt": max(dts) if dts else float("nan"),
        "t_to_180": time_to_temp(rows, 180.0),
        "t_to_193": time_to_temp(rows, 193.0),  # first-crack-ish drop point seen on the ReonAI screen capture
        "mean_ror": statistics.mean(rors) if rors else float("nan"),
        "ror_stdev": statistics.pstdev(rors) if len(rors) > 1 else 0.0,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csvs", nargs="+", help="roast CSV files to compare")
    ap.add_argument("--agtron", help="optional CSV: file,agtron")
    args = ap.parse_args()

    agtron = {}
    if args.agtron:
        with open(args.agtron) as f:
            for r in csv.DictReader(f):
                agtron[r["file"]] = float(r["agtron"])

    summaries = []
    for path_str in args.csvs:
        path = Path(path_str)
        if not path.exists():
            print(f"skip (not found): {path}", file=sys.stderr)
            continue
        rows, meta = load_roast(path)
        if not rows:
            print(f"skip (empty): {path}", file=sys.stderr)
            continue
        s = summarize(path.name, rows, meta)
        if path.name in agtron:
            s["agtron"] = agtron[path.name]
        summaries.append(s)

    if not summaries:
        print("No roasts loaded.", file=sys.stderr)
        sys.exit(1)

    cols = ["name", "bean_type", "roast_level", "setpoint_c", "duration_s", "max_dt", "t_to_180", "t_to_193", "mean_ror", "ror_stdev"]
    if agtron:
        cols.append("agtron")
    print(",".join(cols))
    for s in summaries:
        print(",".join(str(round(s[c], 2)) if isinstance(s.get(c), float) else str(s.get(c, "")) for c in cols))

    print()
    t193 = [s["t_to_193"] for s in summaries if s["t_to_193"] is not None]
    if len(t193) > 1:
        mean = statistics.mean(t193)
        sd = statistics.pstdev(t193)
        cv = (sd / mean * 100) if mean else float("nan")
        print(f"time-to-193C across {len(t193)} roasts: mean={mean:.1f}s stdev={sd:.1f}s "
              f"(coefficient of variation {cv:.1f}%)")
        print("Lower CV = more repeatable. Compare this number against a batch of manually-roasted")
        print("runs of the same profile before concluding the AI/monitored approach is worth building on.")
    else:
        print("Need at least 2 roasts with a valid time-to-193C to compute repeatability.")

    if agtron:
        pairs = [(s["ror_stdev"], s["agtron"]) for s in summaries if "agtron" in s]
        if len(pairs) > 2:
            xs, ys = zip(*pairs)
            mean_x, mean_y = statistics.mean(xs), statistics.mean(ys)
            cov = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
            denom = (sum((x - mean_x) ** 2 for x in xs) ** 0.5) * (sum((y - mean_y) ** 2 for y in ys) ** 0.5)
            corr = cov / denom if denom else float("nan")
            print(f"\ncorrelation(RoR stdev, Agtron) = {corr:.2f} over {len(pairs)} roasts")
            print("(this is a rough signal, not a real statistical test — get more roasts before trusting it)")


if __name__ == "__main__":
    main()
