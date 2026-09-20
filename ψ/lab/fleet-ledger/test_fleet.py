"""Offline tests for fleet.py — no network, no real agents. Run: uv run --no-project --with pytest pytest -q"""
import fcntl
import json
import os
import shlex
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE / "fleet.py"
sys.path.insert(0, str(HERE))
import fleet  # noqa: E402


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    p = tmp_path / "logs" / "fleet-ledger.jsonl"
    monkeypatch.setenv("FLEET_LEDGER", str(p))
    return p


def rows(p):
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def add_sent(agent="agy", label="t", rid=None):
    rid = rid or str(uuid.uuid4())
    fleet.append_event({"ev": "sent", "id": rid, "agent": agent, "label": label,
                        "prompt_sha256": None, "prompt_len": None, "access": "unknown"})
    return rid


def add_done(rid, status="ok"):
    fleet.append_event({"ev": "done", "id": rid, "status": status, "exit": 0, "duration_s": 1.0, "output_len": None})


def cli(*args, **kw):
    return subprocess.run([sys.executable, str(FLEET), *args], capture_output=True, text=True, **kw)


def wait_for(cond, timeout=8.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.05)
    return False


# ---- A2 / A7 / A9: flow and state rules ----

def test_sent_pending_done_flow(ledger, capsys):
    rid = add_sent(label="ask grok about exit rule")
    assert fleet.main(["pending"]) == 0
    out = capsys.readouterr().out
    assert rid[:8] in out and "ask grok about exit rule" in out
    add_done(rid)
    fleet.main(["pending"])
    assert "nothing pending" in capsys.readouterr().out


def test_abandon_removes_from_pending_and_is_logged(ledger, capsys):
    rid = add_sent()
    assert fleet.main(["abandon", rid, "--reason", "never came back"]) == 0
    capsys.readouterr()
    fleet.main(["pending"])
    assert "nothing pending" in capsys.readouterr().out
    fleet.main(["recent"])
    assert "abandoned" in capsys.readouterr().out
    assert rows(ledger)[-1]["ev"] == "abandoned"


def test_state_rules(ledger):
    rid = add_sent()
    with pytest.raises(fleet.Rejected):
        add_sent(rid=rid)                       # duplicate sent
    with pytest.raises(fleet.Rejected):
        add_done(str(uuid.uuid4()))             # unknown id
    with pytest.raises(fleet.Rejected):
        fleet.append_event({"ev": "checked", "id": str(uuid.uuid4()), "claims_total": 1, "claims_wrong": 0})
    add_done(rid)
    with pytest.raises(fleet.Rejected):
        add_done(rid)                           # second done
    with pytest.raises(fleet.Rejected):
        fleet.append_event({"ev": "abandoned", "id": rid, "reason": "x"})   # abandoned after done
    rid2 = add_sent()
    fleet.append_event({"ev": "abandoned", "id": rid2, "reason": "x"})
    with pytest.raises(fleet.Rejected):
        add_done(rid2)                          # done after abandoned
    for _ in range(2):                          # checked: any state, repeatable
        fleet.append_event({"ev": "checked", "id": rid2, "claims_total": 3, "claims_wrong": 1, "note": None})


def test_recent_shows_checked(ledger, capsys):
    rid = add_sent(label="review")
    add_done(rid)
    fleet.append_event({"ev": "checked", "id": rid, "claims_total": 7, "claims_wrong": 1, "note": None})
    fleet.main(["recent"])
    assert "checked 1/7 wrong" in capsys.readouterr().out


def test_missing_ev_is_malformed(ledger):
    ledger.parent.mkdir(parents=True)
    ledger.write_text('{"v":1,"ts":"2026-09-21T03:00:00+07:00","id":"abc","agent":"agy"}\n')
    events, bad = fleet.read_events()
    assert events == [] and bad == 1


# ---- A4: truncated / garbled tail ----

def test_truncated_tail_warns_and_next_append_survives(ledger, capsys):
    add_sent(label="first")
    with open(ledger, "ab") as f:
        f.write(b'{"v":1,"ev":"do')                  # hand-appended fragment, no newline
    for cmd in (["recent"], ["pending"]):
        assert fleet.main(cmd) == 0
        assert "1 malformed line(s) skipped" in capsys.readouterr().err
    add_sent(label="second")
    events, bad = fleet.read_events()
    assert len(events) == 2 and bad == 1             # the new event was not swallowed by the fragment


# ---- A3: concurrent writers, each with its own fd ----

WORKER = ("import sys,uuid; sys.path.insert(0,%r); import fleet\n"
          "for _ in range(int(sys.argv[2])):\n"
          " fleet.append_event({'ev':'sent','id':str(uuid.uuid4()),'agent':'agy','label':'p',"
          "'prompt_sha256':None,'prompt_len':None,'access':'unknown'}, validate=sys.argv[1]=='1')\n") % str(HERE)


@pytest.mark.parametrize("validate,per", [("0", 50), ("1", 20)])
def test_parallel_writers(ledger, validate, per):
    procs = [subprocess.Popen([sys.executable, "-c", WORKER, validate, str(per)]) for _ in range(5)]
    assert [p.wait(timeout=60) for p in procs] == [0] * 5
    events, bad = fleet.read_events()
    assert bad == 0 and len(events) == 5 * per
    assert len({e["id"] for e in events}) == 5 * per


def test_ledger_file_mode_is_private(ledger):
    add_sent()
    assert (os.stat(ledger).st_mode & 0o777) == 0o600


# ---- A6: no prompt text, label limits ----

def test_label_limit_is_characters_not_bytes(ledger):
    assert cli("log", "sent", "--agent", "grokbot", "--label", "ก" * 200).returncode == 0   # 600 bytes, 200 chars
    r = cli("log", "sent", "--agent", "grokbot", "--label", "x" * 201)
    assert r.returncode == 2 and "limit 200" in r.stderr


def test_secret_prompt_never_reaches_file(ledger, tmp_path):
    pf = tmp_path / "p.txt"
    pf.write_text("please use key sk-SECRET-123 now", encoding="utf-8")
    r = cli("log", "sent", "--agent", "grokbot", "--label", "x", "--prompt-file", str(pf))
    assert r.returncode == 0 and str(uuid.UUID(r.stdout.strip())) == r.stdout.strip()
    r = cli("run", "--agent", "agy", "--label", "y", "--", sys.executable, "-c", "pass", "-p", "sk-SECRET-456")
    assert r.returncode == 0
    text = ledger.read_text(encoding="utf-8")
    assert "SECRET" not in text
    first = rows(ledger)[0]
    assert first["prompt_len"] == len("please use key sk-SECRET-123 now") and len(first["prompt_sha256"]) == 64


# ---- `fleet run` ----

CHILD_EXIT3 = "import sys; sys.stdout.write('out\\n'); sys.stderr.write('err\\n'); sys.exit(3)"


def test_run_passthrough_and_exit_code(ledger, tmp_path):
    out = tmp_path / "out.txt"
    with open(out, "wb") as f:
        r = subprocess.run([sys.executable, str(FLEET), "run", "--agent", "agy", "--label", "t", "--",
                            sys.executable, "-c", CHILD_EXIT3], stdout=f, stderr=subprocess.PIPE, text=True)
    assert r.returncode == 3 and r.stderr == "err\n" and out.read_text() == "out\n"
    ev = rows(ledger)
    assert [e["ev"] for e in ev] == ["sent", "done"]
    assert ev[1]["status"] == "error" and ev[1]["exit"] == 3 and ev[1]["output_len"] == 4
    r = cli("run", "--agent", "agy", "--label", "t", "--", sys.executable, "-c", CHILD_EXIT3)   # stdout is a pipe
    assert r.returncode == 3 and r.stdout == "out\n" and r.stderr == "err\n"
    assert rows(ledger)[-1]["output_len"] is None


def test_run_in_background_records_duration(ledger):
    p = subprocess.Popen([sys.executable, str(FLEET), "run", "--agent", "zcode", "--label", "bg", "--",
                          sys.executable, "-c", "import time; time.sleep(1.2)"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert wait_for(lambda: ledger.exists() and len(rows(ledger)) >= 1)
    assert cli("pending").stdout.count("bg") == 1          # visible while running
    assert p.wait(timeout=20) == 0
    done = rows(ledger)[-1]
    assert done["ev"] == "done" and done["status"] == "ok" and done["exit"] == 0
    assert 1.0 <= done["duration_s"] <= 6.0


def test_launch_failure_still_writes_done(ledger):
    r = cli("run", "--agent", "agy", "--label", "t", "--", "/nonexistent-binary-xyz")
    assert r.returncode == 127
    ev = rows(ledger)
    assert [e["ev"] for e in ev] == ["sent", "done"] and ev[1]["status"] == "error" and ev[1]["exit"] == 127


def test_timeout_kills_and_records(ledger):
    t0 = time.monotonic()
    r = cli("run", "--agent", "agy", "--label", "t", "--timeout", "1", "--",
            sys.executable, "-c", "import time; time.sleep(30)")
    assert r.returncode == 124 and time.monotonic() - t0 < 15
    done = rows(ledger)[-1]
    assert done["status"] == "timeout" and done["exit"] == 124


def test_sigterm_is_forwarded_and_recorded(ledger):
    p = subprocess.Popen([sys.executable, str(FLEET), "run", "--agent", "agy", "--label", "t", "--",
                          sys.executable, "-c", "import time; time.sleep(30)"])
    assert wait_for(lambda: ledger.exists() and len(rows(ledger)) >= 1)
    p.send_signal(signal.SIGTERM)                            # no sleep: handlers are installed before launch, an early signal is queued
    assert p.wait(timeout=10) == 143
    done = rows(ledger)[-1]
    assert done["ev"] == "done" and done["status"] == "error" and done["exit"] == 143


def test_lock_busy_is_fail_open(ledger):
    ledger.parent.mkdir(parents=True)
    fd = os.open(ledger, os.O_WRONLY | os.O_CREAT, 0o600)
    fcntl.flock(fd, fcntl.LOCK_EX)
    try:
        env = {**os.environ, "FLEET_LOCK_WAIT_S": "0.3"}
        r = cli("run", "--agent", "agy", "--label", "t", "--", sys.executable, "-c", "print('hi')", env=env)
    finally:
        os.close(fd)
    assert r.returncode == 0 and r.stdout == "hi\n" and "could not record start" in r.stderr
    assert fleet.read_events() == ([], 0)                    # nothing written, and no orphan done either


def test_duplicate_user_id_aborts_before_launch(ledger, tmp_path):
    rid = add_sent()
    marker = tmp_path / "ran"
    r = cli("run", "--agent", "agy", "--label", "t", "--id", rid, "--",
            sys.executable, "-c", f"open({str(marker)!r}, 'w')")
    assert r.returncode == 2 and "duplicate id" in r.stderr and not marker.exists()


# ---- argv inspection ----

def test_zcode_resolution():
    assert fleet.resolve_command(["zcode", "-p", "x"]) == fleet.ZCODE_CMD + ["-p", "x"]
    assert fleet.resolve_command(["agy", "-p", "x"]) == ["agy", "-p", "x"]


@pytest.mark.parametrize("argv,prompt,access", [
    (["agy", "-p", "hello", "--mode", "plan"], "hello", "read-only"),
    (["zcode", "-p", "review", "--cwd", "/x", "--disallowedTools", "Edit Write Bash"], "review", "read-only"),
    (["zcode", "--prompt=hi", "--disallowedTools=Edit Write"], "hi", "read-only"),
    (["grok", "-p", "fix", "--cwd", "/x", "--yolo"], "fix", "write"),
    (["agy", "-p", "x", "--mode", "accept-edits"], "x", "write"),
    (["agy", "--model", "gemini-3.1-pro-high", "-p", "x"], "x", "unknown"),
    (["zcode", "-p", "x", "--disallowedTools", "Edit"], "x", "unknown"),
    (["echo", "hello"], "echo hello", "unknown"),
])
def test_inspect_argv(argv, prompt, access):
    assert fleet.inspect_argv(argv) == (prompt, access)


# ---- added after the code/test review (zcode + agy, 2026-09-21) ----

def test_pending_marks_stale(ledger, capsys):
    ledger.parent.mkdir(parents=True)
    old = (datetime.now().astimezone() - timedelta(hours=13)).isoformat(timespec="seconds")
    new = (datetime.now().astimezone() - timedelta(hours=1)).isoformat(timespec="seconds")
    base = {"v": 1, "ev": "sent", "agent": "grokbot", "prompt_sha256": None, "prompt_len": None, "access": "unknown"}
    ledger.write_text(json.dumps({**base, "ts": old, "id": "old-1", "label": "old one"}) + "\n" +
                      json.dumps({**base, "ts": new, "id": "new-1", "label": "new one"}) + "\n", encoding="utf-8")
    fleet.main(["pending"])
    out = capsys.readouterr().out
    assert [("STALE" in line) for line in out.splitlines() if "old one" in line or "new one" in line] == [True, False]


def test_recent_on_empty_or_missing_ledger(ledger, capsys):
    assert fleet.main(["recent"]) == 0
    assert "ledger is empty" in capsys.readouterr().out
    assert fleet.main(["pending"]) == 0 and "nothing pending" in capsys.readouterr().out


def test_new_events_are_timezone_aware_and_thai_roundtrips(ledger):
    assert cli("log", "sent", "--agent", "grokbot", "--label", "ถาม Grok เรื่องกฎออก").returncode == 0
    ev = rows(ledger)[0]
    assert datetime.fromisoformat(ev["ts"]).tzinfo is not None
    assert ev["label"] == "ถาม Grok เรื่องกฎออก" and "ถาม" in ledger.read_text(encoding="utf-8")   # not \u-escaped


@pytest.mark.parametrize("mutate", [
    lambda o: o.pop("id"), lambda o: o.pop("v"), lambda o: o.pop("ts"), lambda o: o.pop("ev"),
    lambda o: o.update(ts="2026-09-21T03:00:00"),          # naive timestamp
    lambda o: o.update(agent=[]), lambda o: o.update(label={"x": 1}), lambda o: o.update(prompt_len="9"),
    lambda o: o.update(v=True), lambda o: o.update(ev="nope"),
])
def test_valid_event_rejects_bad_lines(mutate):
    good = {"v": 1, "ev": "sent", "ts": "2026-09-21T03:00:00+07:00", "id": "x", "agent": "agy", "label": "l",
            "prompt_sha256": None, "prompt_len": 3, "access": "unknown"}
    assert fleet.valid_event(good)
    bad = dict(good)
    mutate(bad)
    assert not fleet.valid_event(bad)


def test_wrong_typed_but_parseable_line_does_not_crash_readers(ledger, capsys):
    ledger.parent.mkdir(parents=True)
    ledger.write_text('{"v":1,"ev":"sent","ts":"2026-09-21T10:00:00+07:00","id":"abc","agent":[],"label":"x",'
                      '"prompt_sha256":null,"prompt_len":null,"access":"read-only"}\n', encoding="utf-8")
    for cmd in (["pending"], ["recent"]):
        assert fleet.main(cmd) == 0
        assert "1 malformed line(s) skipped" in capsys.readouterr().err


def test_run_output_len_with_append_redirect(ledger, tmp_path):
    out = tmp_path / "out.log"
    out.write_bytes(b"x" * 1000)                              # pre-existing content
    # a real shell `>>` (Python's open("ab") would seek to the end by itself and hide the problem)
    cmd = (f"{shlex.quote(sys.executable)} {shlex.quote(str(FLEET))} run --agent agy --label t -- "
           f"{shlex.quote(sys.executable)} -c \"print('out')\" >> {shlex.quote(str(out))}")
    r = subprocess.run(["sh", "-c", cmd], capture_output=True, text=True)
    assert r.returncode == 0 and out.stat().st_size == 1004
    assert rows(ledger)[-1]["output_len"] == 4                # not 1004


def test_timeout_must_be_positive(ledger, tmp_path):
    marker = tmp_path / "ran"
    r = cli("run", "--agent", "agy", "--label", "t", "--timeout", "0", "--",
            sys.executable, "-c", f"open({str(marker)!r}, 'w')")
    assert r.returncode == 2 and "--timeout must be > 0" in r.stderr and not marker.exists()
    assert not ledger.exists() or rows(ledger) == []


def test_sigint_is_forwarded_with_timeout(ledger):
    p = subprocess.Popen([sys.executable, str(FLEET), "run", "--agent", "agy", "--label", "t", "--timeout", "60", "--",
                          sys.executable, "-c", "import time; time.sleep(30)"], stderr=subprocess.DEVNULL)
    assert wait_for(lambda: ledger.exists() and len(rows(ledger)) >= 1)
    p.send_signal(signal.SIGINT)
    assert p.wait(timeout=10) != 0
    done = rows(ledger)[-1]
    assert done["ev"] == "done" and done["status"] == "error"


def test_second_sigint_escalates_without_timeout(ledger, tmp_path):
    ready = tmp_path / "ready"
    child = f"import time, signal; signal.signal(signal.SIGINT, signal.SIG_IGN); open({str(ready)!r}, 'w').close(); time.sleep(30)"
    p = subprocess.Popen([sys.executable, str(FLEET), "run", "--agent", "agy", "--label", "t", "--",
                          sys.executable, "-c", child], stderr=subprocess.DEVNULL)
    assert wait_for(ready.exists)
    p.send_signal(signal.SIGINT)                              # 1st: ignored by design (the terminal already told the child)
    time.sleep(0.5)
    assert p.poll() is None
    p.send_signal(signal.SIGINT)                              # 2nd: child gets SIGKILL
    assert p.wait(timeout=10) == 137
    assert rows(ledger)[-1]["exit"] == 137


def test_inspect_argv_dangling_prompt_still_reads_access_flags():
    prompt, access = fleet.inspect_argv(["zcode", "--mode", "plan", "-p"])
    assert access == "read-only" and prompt == "zcode --mode plan -p"
    assert fleet.inspect_argv(["agy", "--yolo", "-p"])[1] == "write"


def test_comma_separated_disallowed_tools():
    assert fleet.inspect_argv(["zcode", "-p", "x", "--disallowedTools", "Edit,Write"])[1] == "read-only"


def test_bad_lock_wait_env_does_not_break_readers(ledger, monkeypatch, capsys):
    monkeypatch.setenv("FLEET_LOCK_WAIT_S", "abc")
    assert fleet.lock_wait_s() == 5.0
    assert fleet.main(["recent"]) == 0
