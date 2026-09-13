#!/usr/bin/env python3
"""
Classify each ayami-oracle session retrospective as PENDING / DONE / UNKNOWN / NO-AUDIT
by parsing the "## 🔍 Self-Audit" block's `blocked:` and `next steps:` lines.

Usage:
    python3 session_status.py                  # table, newest first
    python3 session_status.py --status pending  # only PENDING rows
    python3 session_status.py --json            # machine-readable
"""
import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RETRO_DIR = REPO_ROOT / "ψ" / "memory" / "retrospectives"

SESSION_RE = re.compile(r"📡\s*Session:\s*`?([^\s|`]+)")
AUDIT_HEADER_RE = re.compile(r"^#+\s*.*Self-Audit", re.IGNORECASE | re.MULTILINE)
# Stop the Self-Audit block at the next markdown heading. Known limitation: this
# doesn't track heading depth, so a deeper sub-heading inside the block (rare in
# this corpus) would cut it short rather than being treated as nested content.
NEXT_HEADING_RE = re.compile(r"\n#{1,3}\s", re.MULTILINE)
BLOCKED_RE = re.compile(r"[-*]?\s*\bblocked:\s*(.+)", re.IGNORECASE)
NEXT_STEPS_RE = re.compile(r"[-*]?\s*\bnext[- ]steps?:\s*(.+)", re.IGNORECASE)
LEADING_INT_RE = re.compile(r"^\s*(\d+)")
NONE_WORD_RE = re.compile(r"^\s*(none|0|no)\b", re.IGNORECASE)


def extract_int_field(line: str):
    """Return (count_or_None, raw_text). count is None when unparseable (not 0)."""
    line = line.strip()
    if NONE_WORD_RE.match(line):
        # "none remaining", "none this leg" etc. -> explicit zero
        return 0, line
    m = LEADING_INT_RE.match(line)
    if m:
        return int(m.group(1)), line
    return None, line  # unparseable, e.g. "blocked: waiting on user"


def find_self_audit_block(text: str):
    m = AUDIT_HEADER_RE.search(text)
    if not m:
        return None
    start = m.end()
    rest = text[start:]
    end_m = NEXT_HEADING_RE.search(rest)
    return rest[: end_m.start()] if end_m else rest


def classify(path: Path):
    text = path.read_text(errors="replace")

    session_ids = SESSION_RE.findall(text)
    session_id = session_ids[0] if session_ids else None
    session_id_warning = None
    if len(session_ids) == 0:
        session_id_warning = "no 📡 Session: header found"
    elif len(session_ids) > 1:
        session_id_warning = f"{len(session_ids)} 📡 Session: headers found (using first)"

    audit_block = find_self_audit_block(text)
    if audit_block is None:
        return {
            "path": str(path.relative_to(REPO_ROOT)),
            "session_id": session_id,
            "session_id_warning": session_id_warning,
            "status": "NO-AUDIT",
            "reason": "no ## Self-Audit section in file",
            "blocked_raw": None,
            "next_steps_raw": None,
        }

    blocked_m = BLOCKED_RE.search(audit_block)
    next_steps_m = NEXT_STEPS_RE.search(audit_block)

    blocked_count, blocked_raw = (None, None)
    if blocked_m:
        blocked_count, blocked_raw = extract_int_field(blocked_m.group(1))

    next_steps_count, next_steps_raw = (None, None)
    if next_steps_m:
        next_steps_count, next_steps_raw = extract_int_field(next_steps_m.group(1))

    if blocked_m is None and next_steps_m is None:
        return {
            "path": str(path.relative_to(REPO_ROOT)),
            "session_id": session_id,
            "session_id_warning": session_id_warning,
            "status": "NO-AUDIT",
            "reason": "Self-Audit section present but no blocked:/next steps: lines matched",
            "blocked_raw": None,
            "next_steps_raw": None,
        }

    if blocked_count is None or next_steps_count is None:
        # At least one field didn't parse as a number -> don't guess, surface it.
        pieces = []
        if blocked_count is None and blocked_raw is not None:
            pieces.append(f"blocked unparseable: \"{blocked_raw[:80]}\"")
        if next_steps_count is None and next_steps_raw is not None:
            pieces.append(f"next steps unparseable: \"{next_steps_raw[:80]}\"")
        return {
            "path": str(path.relative_to(REPO_ROOT)),
            "session_id": session_id,
            "session_id_warning": session_id_warning,
            "status": "UNKNOWN",
            "reason": "; ".join(pieces) if pieces else "unparseable Self-Audit fields",
            "blocked_raw": blocked_raw,
            "next_steps_raw": next_steps_raw,
        }

    if blocked_count == 0 and next_steps_count == 0:
        return {
            "path": str(path.relative_to(REPO_ROOT)),
            "session_id": session_id,
            "session_id_warning": session_id_warning,
            "status": "DONE",
            "reason": "blocked: 0, next steps: 0",
            "blocked_raw": blocked_raw,
            "next_steps_raw": next_steps_raw,
        }

    triggers = []
    if blocked_count and blocked_count >= 1:
        triggers.append(f"blocked={blocked_count} (\"{(blocked_raw or '')[:100]}\")")
    if next_steps_count and next_steps_count >= 1:
        triggers.append(f"next_steps={next_steps_count} (\"{(next_steps_raw or '')[:100]}\")")

    return {
        "path": str(path.relative_to(REPO_ROOT)),
        "session_id": session_id,
        "session_id_warning": session_id_warning,
        "status": "PENDING",
        "reason": " | ".join(triggers),
        "blocked_raw": blocked_raw,
        "next_steps_raw": next_steps_raw,
    }


def date_key_from_path(path: Path):
    # Expected: ψ/memory/retrospectives/YYYY-MM/DD/HH.MM_slug.md
    parts = path.relative_to(RETRO_DIR).parts
    try:
        year_month, day, filename = parts[0], parts[1], parts[-1]
        time_part = filename.split("_", 1)[0]
        if not re.match(r"^\d{4}-\d{2}$", year_month) or not re.match(r"^\d{2}$", day) \
                or not re.match(r"^\d{2}\.\d{2}$", time_part):
            raise ValueError("doesn't match YYYY-MM/DD/HH.MM_ layout")
        return f"{year_month}-{day} {time_part.replace('.', ':')}"
    except Exception as e:
        print(f"WARNING: {path} doesn't match expected retro path layout ({e}); "
              f"sorted last, included in counts anyway", file=sys.stderr)
        return "0000-00-00 00:00"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", choices=["pending", "done", "unknown", "no-audit"], default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    files = sorted(RETRO_DIR.rglob("*.md"))
    if not files:
        print(f"No retrospective files found under {RETRO_DIR}", file=sys.stderr)
        sys.exit(1)

    rows = []
    for f in files:
        row = classify(f)
        row["date_key"] = date_key_from_path(f)
        rows.append(row)

    rows.sort(key=lambda r: r["date_key"], reverse=True)

    if args.status:
        rows = [r for r in rows if r["status"].lower() == args.status]

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return

    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    print(f"{'Date':<16} {'Session ID':<16} {'Status':<9} Reason")
    print("-" * 100)
    for r in rows:
        sid = r["session_id"] or "?"
        warn = f" ⚠{r['session_id_warning']}" if r["session_id_warning"] else ""
        print(f"{r['date_key']:<16} {sid:<16} {r['status']:<9} {r['reason']}{warn}")

    print("-" * 100)
    print("Counts:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    print(f"Note: PENDING/DONE reflects the retro's Self-Audit AT THE TIME IT WAS WRITTEN,")
    print(f"not whether it's still open today — a later session may have already closed it.")


if __name__ == "__main__":
    main()
