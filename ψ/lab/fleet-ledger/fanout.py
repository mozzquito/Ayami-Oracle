#!/usr/bin/env python3
"""fanout — send split-scope review prompts to zcode and agy IN PARALLEL through `fleet run`, read-only, output to files.

  fanout.py --brief FILE --zcode "prompt A" --agy "prompt B" --yes-public [--group NAME] [--timeout 900] [--agy-model M]

Each agent gets a DIFFERENT prompt (split by scope, not the same question twice). Outputs land in
<repo>/.tmp/fanout/<stamp>/{zcode,agy}.{out,err}. Nothing is merged or judged here: Ayami reads the files and checks every claim
against source. Grok Bot is not part of this (asynchronous, may take 20+ minutes). Public / non-sensitive content only:
prompts and the brief go to third-party models, hence the required --yes-public.
Test hooks: env FANOUT_ZCODE_CMD / FANOUT_AGY_CMD replace the agent command (shlex-split).
"""
from __future__ import annotations

import argparse
import os
import shlex
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
FLEET = HERE / "fleet.py"
REPO = HERE.parents[2]
AGY_SUFFIX = ("\n\nPrint your FULL answer directly in your final message to stdout. Do not create artifacts or plan documents, "
              "and do not edit any file.")


def agent_cmd(name: str) -> list:
    override = os.environ.get(f"FANOUT_{name.upper()}_CMD")
    return shlex.split(override) if override else [name]


def build(args, group: str, out_dir: Path):
    brief = str(Path(args.brief).resolve().relative_to(Path(args.cwd).resolve()))  # relative: no local directory names in the prompt
    z_prompt = f"{args.zcode}\n\nBrief file (read it first): {brief}"
    a_prompt = f"{args.agy}\n\nBrief file (read it first): {brief}{AGY_SUFFIX}"
    common = [sys.executable, str(FLEET), "run", "--group", group, "--timeout", str(args.timeout)]
    z = common + ["--agent", "zcode", "--label", f"fanout {group}: zcode", "--"] + agent_cmd("zcode") + [
        "-p", z_prompt, "--cwd", args.cwd, "--disallowedTools", "Edit Write Bash"]
    a = common + ["--agent", "agy", "--label", f"fanout {group}: agy", "--"] + agent_cmd("agy") + [
        "-p", a_prompt, "--mode", "plan"] + (["--model", args.agy_model] if args.agy_model else [])
    return {"zcode": z, "agy": a}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="fanout", description=__doc__.split("\n")[1], allow_abbrev=False)
    p.add_argument("--brief", required=True, help="file the reviewers read (public / non-sensitive only)")
    p.add_argument("--zcode", required=True, help="prompt for zcode")
    p.add_argument("--agy", required=True, help="prompt for agy (a different scope)")
    p.add_argument("--group", help="ledger group name (default fanout-<timestamp>)")
    p.add_argument("--timeout", type=float, default=900.0)
    p.add_argument("--cwd", default=str(REPO))
    p.add_argument("--agy-model")
    p.add_argument("--out-dir")
    p.add_argument("--yes-public", action="store_true",
                   help="confirm the brief and prompts contain NO sensitive data (eVisa/Wayama/PII/secrets)")
    args = p.parse_args(argv)
    if not args.yes_public:
        print("fanout: refusing to run without --yes-public (prompts and brief go to third-party models)", file=sys.stderr)
        return 2
    if not Path(args.brief).is_file():
        print(f"fanout: brief not found: {args.brief}", file=sys.stderr)
        return 2
    try:
        Path(args.brief).resolve().relative_to(Path(args.cwd).resolve())
    except ValueError:
        print(f"fanout: the brief must live inside --cwd ({args.cwd}) so reviewers get a relative path", file=sys.stderr)
        return 2
    if args.timeout <= 0:
        print("fanout: --timeout must be > 0", file=sys.stderr)
        return 2
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    group = args.group or f"fanout-{stamp}"
    out_dir = Path(args.out_dir) if args.out_dir else REPO / ".tmp" / "fanout" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    if any((out_dir / f"{n}.{x}").exists() for n in ("zcode", "agy") for x in ("out", "err")):
        print(f"fanout: {out_dir} already has results; nothing is overwritten, use a new --out-dir", file=sys.stderr)
        return 2

    procs, t0, codes = {}, time.monotonic(), {}

    def _terminate(signum, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, _terminate)  # a plain `kill` must stop the agents too, not orphan them
    interrupted = False
    try:
        for name, cmd in build(args, group, out_dir).items():
            out, err = open(out_dir / f"{name}.out", "wb"), open(out_dir / f"{name}.err", "wb")  # own files: no interleaving
            procs[name] = (subprocess.Popen(cmd, stdout=out, stderr=err, stdin=subprocess.DEVNULL, cwd=args.cwd), out, err)
        for name, (proc, _o, _e) in procs.items():
            codes[name] = proc.wait()
    except KeyboardInterrupt:
        interrupted = True
        for proc, _o, _e in procs.values():
            if proc.poll() is None:
                proc.terminate()  # each `fleet run` wrapper forwards this to its agent and still writes `done`
        for proc, _o, _e in procs.values():
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()
    finally:
        for _p, out, err in procs.values():
            out.close()
            err.close()
    if interrupted:
        print(f"fanout: interrupted, agents told to stop (group {group}, outputs in {out_dir})", file=sys.stderr)
        return 130
    print(f"fanout group={group} finished in {time.monotonic() - t0:.0f}s  ->  {out_dir}")
    for name in procs:
        size = (out_dir / f"{name}.out").stat().st_size
        note = "  (EMPTY: agent may have written an artifact instead of stdout)" if size == 0 else ""
        print(f"  {name:<6} exit {codes[name]:<4} {size:>7} bytes  {out_dir / (name + '.out')}{note}")
    print("Not merged or judged. Read each file and verify its claims against source before acting.")
    return 0 if all(c == 0 for c in codes.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
