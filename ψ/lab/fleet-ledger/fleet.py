#!/usr/bin/env python3
"""fleet — append-only ledger of what Ayami sent to which agent, and whether it came back (see DESIGN.md).

Stdlib only. Ledger: ψ/memory/logs/fleet-ledger.jsonl (git-ignored), override with env FLEET_LEDGER.
Never stores prompt or reply text: label + SHA-256 + length only.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

SCHEMA_V = 1
AGENTS = ("zcode", "agy", "grok-cli", "grokbot")
RUN_AGENTS = ("zcode", "agy", "grok-cli")
STATUSES = ("ok", "error", "timeout")
ACCESS = ("read-only", "write", "unknown")
MAX_LABEL = 200  # characters, not bytes
MAX_LINE = 4096  # bytes, backstop
ZCODE_CMD = ["node", "/Applications/ZCode.app/Contents/Resources/glm/zcode.cjs"]


def lock_wait_s() -> float:
    """Seconds to wait for the ledger lock. Env FLEET_LOCK_WAIT_S overrides (tests); a bad value falls back to 5."""
    try:
        return float(os.environ.get("FLEET_LOCK_WAIT_S", "5"))
    except ValueError:
        return 5.0


def _is_str(x):
    return isinstance(x, str)


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _opt(check):
    return lambda x: x is None or check(x)


# required fields per event type, with a type check for each (a hand-made line with wrong types is "malformed")
FIELD_TYPES = {
    "sent": {"agent": _is_str, "label": _is_str, "prompt_sha256": _opt(_is_str), "prompt_len": _opt(_is_int), "access": _is_str},
    "done": {"status": _is_str},
    "abandoned": {"reason": _is_str},
    "checked": {"claims_total": _is_int, "claims_wrong": _is_int},
}


class LedgerError(Exception):
    pass


class LedgerBusy(LedgerError):
    pass


class Rejected(LedgerError):
    pass


def ledger_path() -> Path:
    env = os.environ.get("FLEET_LEDGER")
    if env:
        return Path(env)
    # fleet.py -> fleet-ledger -> lab -> ψ
    return Path(__file__).resolve().parents[2] / "memory" / "logs" / "fleet-ledger.jsonl"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def parse_ts(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        raise ValueError("naive timestamp")
    return dt


def valid_event(obj) -> bool:
    if not isinstance(obj, dict):
        return False
    ev = obj.get("ev")
    if ev not in FIELD_TYPES or not isinstance(obj.get("id"), str) or not obj.get("id"):
        return False
    if not _is_int(obj.get("v")) or not isinstance(obj.get("ts"), str):
        return False
    try:
        parse_ts(obj["ts"])
    except ValueError:
        return False
    return all(k in obj and check(obj[k]) for k, check in FIELD_TYPES[ev].items())


def read_events(path: Path | None = None):
    """Return (events, malformed_count). Missing file -> ([], 0). Blank lines are ignored."""
    path = path or ledger_path()
    events, bad = [], 0
    try:
        with open(path, "rb") as f:
            for raw in f:
                if not raw.strip():
                    continue
                try:
                    obj = json.loads(raw)
                except ValueError:
                    bad += 1
                    continue
                if valid_event(obj):
                    events.append(obj)
                else:
                    bad += 1
    except FileNotFoundError:
        pass
    return events, bad


def fold(events):
    recs = {}
    for e in events:
        r = recs.setdefault(e["id"], {"sent": None, "end": None, "checks": []})
        ev = e["ev"]
        if ev == "sent":
            if r["sent"] is None:
                r["sent"] = e
        elif ev in ("done", "abandoned"):
            if r["end"] is None:
                r["end"] = e
        else:
            r["checks"].append(e)
    return recs


def check_state_rules(events, obj) -> None:
    recs = fold(events)
    r = recs.get(obj["id"])
    ev = obj["ev"]
    if ev == "sent":
        if r is not None and r["sent"] is not None:
            raise Rejected(f"duplicate id {obj['id']}")
        return
    if r is None or r["sent"] is None:
        raise Rejected(f"unknown id {obj['id']} (no sent event)")
    if ev in ("done", "abandoned") and r["end"] is not None:
        raise Rejected(f"{obj['id']} already ended ({r['end']['ev']})")


def append_event(event: dict, *, validate: bool = True, path: Path | None = None) -> dict:
    path = path or ledger_path()
    obj = {"v": SCHEMA_V, "ev": event["ev"], "ts": now_iso()}
    obj.update({k: v for k, v in event.items() if k != "ev"})
    if not valid_event(obj):
        raise Rejected(f"malformed event: {obj}")
    data = (json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    if len(data) > MAX_LINE:
        raise Rejected(f"event is {len(data)} bytes, limit {MAX_LINE}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        wait = lock_wait_s()
        deadline = time.monotonic() + wait
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise LedgerBusy(f"ledger locked for {wait}s: {path}")
                time.sleep(0.02)
        if validate:
            events, _ = read_events(path)  # separate read-only descriptor, under the same lock
            check_state_rules(events, obj)
        size = os.fstat(fd).st_size
        if size > 0:
            rfd = os.open(path, os.O_RDONLY)
            try:
                if os.pread(rfd, 1, size - 1) != b"\n":
                    data = b"\n" + data  # keep a hand-appended, truncated fragment on its own line
            finally:
                os.close(rfd)
        view = memoryview(data)
        while view:
            n = os.write(fd, view)
            view = view[n:]
    finally:
        os.close(fd)  # releases the flock
    return obj


# ---------- argv inspection for `fleet run` ----------

class _Quiet(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def resolve_command(argv):
    return ZCODE_CMD + list(argv[1:]) if argv and argv[0] == "zcode" else list(argv)


def inspect_argv(argv):
    """Return (prompt_text, access) guessed from the child's argv. Advisory only."""
    p = _Quiet(add_help=False, allow_abbrev=False)
    p.add_argument("-p", "--prompt", "--print", dest="prompt")
    p.add_argument("--disallowedTools", dest="disallowed", nargs="+")
    p.add_argument("--mode")
    p.add_argument("--yolo", action="store_true")
    p.add_argument("--dangerously-skip-permissions", action="store_true", dest="skip")
    try:
        ns, _ = p.parse_known_args(list(argv[1:]))
    except ValueError:  # e.g. a dangling `-p`: still read the access flags by a plain token scan
        toks = list(argv[1:])
        mode = None
        for i, t in enumerate(toks):
            if t == "--mode" and i + 1 < len(toks):
                mode = toks[i + 1]
            elif t.startswith("--mode="):
                mode = t[len("--mode="):]
        if "--yolo" in toks or "--dangerously-skip-permissions" in toks or mode == "accept-edits":
            return " ".join(argv), "write"
        return " ".join(argv), "read-only" if mode == "plan" else "unknown"
    prompt = ns.prompt if ns.prompt is not None else " ".join(argv)
    if ns.yolo or ns.skip or ns.mode == "accept-edits":
        return prompt, "write"
    tools = set(re.split(r"[\s,]+", " ".join(ns.disallowed or [])))
    if ns.mode == "plan" or {"Edit", "Write"} <= tools:
        return prompt, "read-only"
    return prompt, "unknown"


def prompt_fields(text):
    if text is None:
        return None, None
    return hashlib.sha256(text.encode("utf-8")).hexdigest(), len(text)


# ---------- formatting ----------

def fmt_secs(s: float) -> str:
    s = int(s)
    if s < 90:
        return f"{s}s"
    m = s // 60
    if m < 60:
        return f"{m}m"
    return f"{m // 60}h{m % 60:02d}m"


def warn(msg: str) -> None:
    print(msg, file=sys.stderr)


def warn_bad(bad: int) -> None:
    if bad:
        warn(f"warning: {bad} malformed line(s) skipped")


def die(msg: str, code: int = 2) -> int:
    warn(f"fleet: {msg}")
    return code


def check_label(label: str) -> None:
    if not label or not label.strip():
        raise Rejected("label is empty")
    if len(label) > MAX_LABEL:
        raise Rejected(f"label is {len(label)} characters, limit {MAX_LABEL}")


def norm_id(s: str) -> str:
    try:
        return str(uuid.UUID(s))
    except ValueError:
        raise Rejected(f"not a UUID: {s!r}")


# ---------- commands ----------

def cmd_log_sent(a):
    check_label(a.label)
    rid = norm_id(a.id) if a.id else str(uuid.uuid4())
    text = None
    if a.prompt_file:
        raw = sys.stdin.buffer.read() if a.prompt_file == "-" else Path(a.prompt_file).read_bytes()
        text = raw.decode("utf-8", errors="replace")
    sha, ln = prompt_fields(text)
    append_event({"ev": "sent", "id": rid, "agent": a.agent, "label": a.label,
                  "prompt_sha256": sha, "prompt_len": ln, "access": a.access})
    print(rid)
    return 0


def cmd_log_done(a):
    rid = norm_id(a.id)
    append_event({"ev": "done", "id": rid, "status": a.status, "exit": a.exit,
                  "duration_s": a.duration_s, "output_len": a.output_len})
    print(f"{rid[:8]} done {a.status}")
    return 0


def cmd_log_checked(a):
    rid = norm_id(a.id)
    if a.total < 0 or a.wrong < 0 or a.wrong > a.total:
        raise Rejected("need 0 <= wrong <= total")
    if a.note is not None and len(a.note) > MAX_LABEL:
        raise Rejected(f"note is {len(a.note)} characters, limit {MAX_LABEL}")
    append_event({"ev": "checked", "id": rid, "claims_total": a.total, "claims_wrong": a.wrong, "note": a.note})
    print(f"{rid[:8]} checked {a.wrong}/{a.total} wrong")
    return 0


def cmd_abandon(a):
    rid = norm_id(a.id)
    append_event({"ev": "abandoned", "id": rid, "reason": a.reason})
    print(f"{rid[:8]} abandoned")
    return 0


def cmd_pending(a):
    events, bad = read_events()
    warn_bad(bad)
    now = datetime.now().astimezone()
    rows = []
    for rid, r in fold(events).items():
        if r["sent"] is not None and r["end"] is None:
            age = (now - parse_ts(r["sent"]["ts"])).total_seconds()
            rows.append((age, rid, r["sent"]))
    if not rows:
        print("nothing pending")
        return 0
    rows.sort(reverse=True)
    print(f"{'ID':<9} {'AGENT':<9} {'AGE':<7} LABEL")
    for age, rid, s in rows:
        stale = "STALE  " if age > a.stale_hours * 3600 else ""
        print(f"{rid[:8]:<9} {s['agent']:<9} {fmt_secs(age):<7} {stale}{s['label']}")
    return 0


def cmd_recent(a):
    events, bad = read_events()
    warn_bad(bad)
    recs = [r for r in fold(events).values() if r["sent"] is not None]
    recs.sort(key=lambda r: parse_ts(r["sent"]["ts"]), reverse=True)
    now = datetime.now().astimezone()
    for r in recs[: a.n]:
        s, end = r["sent"], r["end"]
        if end is None:
            state, dur = "pending", fmt_secs((now - parse_ts(s["ts"])).total_seconds())
        else:
            state = end["status"] if end["ev"] == "done" else "abandoned"
            d = end.get("duration_s")
            dur = fmt_secs(d) if isinstance(d, (int, float)) else "-"
        chk = ""
        if r["checks"]:
            c = r["checks"][-1]
            chk = f"checked {c['claims_wrong']}/{c['claims_total']} wrong"
        print(f"{s['ts'][:16].replace('T', ' ')}  {s['agent']:<9} {state:<9} {dur:<6} {chk:<20} {s['label']}")
    if not recs:
        print("ledger is empty")
    return 0


def _pos(fd: int):
    """Write position of fd for measuring how much a child wrote; None if not measurable.
    An O_APPEND fd (`>>`) starts at offset 0 whatever the file size, so use the file size there."""
    try:
        if fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_APPEND:
            return os.fstat(fd).st_size
        return os.lseek(fd, 0, os.SEEK_CUR)
    except OSError:
        return None


def cmd_run(a, tail):
    if not tail:
        return die("no command after --")
    if a.timeout is not None and a.timeout <= 0:
        return die("--timeout must be > 0")
    check_label(a.label)
    rid = norm_id(a.id) if a.id else str(uuid.uuid4())
    prompt, inferred = inspect_argv(tail)
    sha, ln = prompt_fields(prompt)
    sent = {"ev": "sent", "id": rid, "agent": a.agent, "label": a.label,
            "prompt_sha256": sha, "prompt_len": ln, "access": a.access or inferred}
    # Signal handlers go in BEFORE anything is launched, so a SIGTERM in the gap cannot kill the wrapper
    # without a `done`: a signal that arrives before the child exists is queued and forwarded right after spawn.
    new_session = a.timeout is not None
    state = {"proc": None, "pending": [], "sigint": 0}

    def send(signum):
        proc = state["proc"]
        try:
            if new_session:
                os.killpg(proc.pid, signum)
            else:
                proc.send_signal(signum)
        except (ProcessLookupError, PermissionError):
            pass

    def on_signal(signum, _frame):
        if signum == signal.SIGINT and not new_session:
            # the terminal already delivered Ctrl-C to the child's process group; a 2nd Ctrl-C escalates to SIGKILL
            state["sigint"] += 1
            if state["sigint"] < 2:
                return
            signum = signal.SIGKILL
        if state["proc"] is None:
            state["pending"].append(signum)
        else:
            send(signum)

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)

    sent_ok = False
    try:
        append_event(sent, validate=bool(a.id))
        sent_ok = True
    except Rejected as e:  # e.g. duplicate user-supplied id: nothing has run yet
        return die(str(e))
    except (LedgerError, OSError) as e:
        warn(f"fleet: could not record start ({e}); running the command anyway")

    def finish(status, code, dur, out_len):
        if not sent_ok:
            return
        try:
            append_event({"ev": "done", "id": rid, "status": status, "exit": code,
                          "duration_s": round(dur, 1), "output_len": out_len}, validate=False)
        except (LedgerError, OSError) as e:
            warn(f"fleet: could not record end ({e})")

    cmd = resolve_command(tail)
    stdin = subprocess.DEVNULL if new_session and sys.stdin is not None and sys.stdin.isatty() else None
    start_off, t0 = _pos(1), time.monotonic()
    try:
        proc = subprocess.Popen(cmd, stdin=stdin, start_new_session=new_session)
    except OSError as e:
        warn(f"fleet: cannot start {cmd[0]}: {e}")
        code = 127 if isinstance(e, FileNotFoundError) else 126
        finish("error", code, time.monotonic() - t0, None)
        return code
    state["proc"] = proc
    for queued in list(state["pending"]):
        send(queued)

    timed_out = False
    try:
        proc.wait(timeout=a.timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        send(signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            send(signal.SIGKILL)
            proc.wait()
    rc = proc.returncode
    code = 124 if timed_out else (rc if rc >= 0 else 128 - rc)
    end_off = _pos(1)
    out_len = end_off - start_off if start_off is not None and end_off is not None and end_off >= start_off else None
    status = "timeout" if timed_out else ("ok" if rc == 0 else "error")
    finish(status, code, time.monotonic() - t0, out_len)
    return code


def build_parser():
    p = argparse.ArgumentParser(prog="fleet", description="Append-only ledger of agent calls (see DESIGN.md).")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run a CLI agent command and record sent/done (command goes after --)")
    r.add_argument("--agent", choices=RUN_AGENTS, required=True)
    r.add_argument("--label", required=True)
    r.add_argument("--id")
    r.add_argument("--access", choices=ACCESS)
    r.add_argument("--timeout", type=float)

    lg = sub.add_parser("log", help="record an event by hand").add_subparsers(dest="what", required=True)
    s = lg.add_parser("sent")
    s.add_argument("--agent", choices=AGENTS, required=True)
    s.add_argument("--label", required=True)
    s.add_argument("--id")
    s.add_argument("--prompt-file")
    s.add_argument("--access", choices=ACCESS, default="unknown")
    d = lg.add_parser("done")
    d.add_argument("--id", required=True)
    d.add_argument("--status", choices=STATUSES, required=True)
    d.add_argument("--exit", type=int)
    d.add_argument("--duration-s", type=float)
    d.add_argument("--output-len", type=int)
    c = lg.add_parser("checked")
    c.add_argument("--id", required=True)
    c.add_argument("--total", type=int, required=True)
    c.add_argument("--wrong", type=int, required=True)
    c.add_argument("--note")

    ab = sub.add_parser("abandon", help="mark a pending id as abandoned")
    ab.add_argument("id")
    ab.add_argument("--reason", required=True)

    pe = sub.add_parser("pending", help="sent with no done/abandoned")
    pe.add_argument("--stale-hours", type=float, default=12.0)
    rc = sub.add_parser("recent", help="latest calls")
    rc.add_argument("n", type=int, nargs="?", default=10)
    return p


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    tail = None
    if "--" in argv:
        i = argv.index("--")
        argv, tail = argv[:i], argv[i + 1:]
    a = build_parser().parse_args(argv)
    if tail is not None and a.cmd != "run":
        return die("'--' is only used with 'run'")
    try:
        if a.cmd == "run":
            return cmd_run(a, tail)
        if a.cmd == "log":
            return {"sent": cmd_log_sent, "done": cmd_log_done, "checked": cmd_log_checked}[a.what](a)
        return {"abandon": cmd_abandon, "pending": cmd_pending, "recent": cmd_recent}[a.cmd](a)
    except (LedgerError, OSError) as e:
        return die(str(e))


if __name__ == "__main__":
    sys.exit(main())
