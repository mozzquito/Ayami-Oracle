#!/usr/bin/env python3
"""
Merge memory-horizon's report.html (LIVE/COOLING/DORMANT/DEPRECATED/LOST — recency-based)
with session_status.py's DONE classification (Self-Audit based) into one dashboard,
stripped down to Artifact-publishable content (no <html>/<head>/<body> wrapper).

Usage:
    python3 build_dashboard.py                        # writes dashboard.html next to this script
    python3 build_dashboard.py -o /path/out.html       # custom output path
    python3 build_dashboard.py --refresh-source        # also re-run memory-horizon + report.html first

Output is written under ψ/incubate/ (gitignored) — never commit it, it contains real
session IDs and conversation excerpts. To publish as a Claude Artifact, hand the output
file's path to Claude and ask it to publish (private by default).
"""
import argparse
import html
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
SOURCE_REPORT = REPO_ROOT / "ψ" / "incubate" / "memory-horizon-cron" / "report.html"
DAILY_CRON = REPO_ROOT / "ψ" / "incubate" / "memory-horizon-cron" / "daily-cron.sh"
DEFAULT_OUT = REPO_ROOT / "ψ" / "incubate" / "memory-horizon-cron" / "dashboard.html"

sys.path.insert(0, str(SCRIPT_DIR))
import session_status as ss  # noqa: E402

SUMMARY_RE = re.compile(r"^#+\s*Session Summary\s*$", re.IGNORECASE | re.MULTILINE)
NEXT_SECTION_RE = re.compile(r"\n#{1,3}\s", re.MULTILINE)
MD_STRIP_RE = re.compile(r"[`*_\[\]]")


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def summary_title(retro_path: Path, max_len: int = 140) -> str:
    """Pull a short title from the retro's '## Session Summary' first sentence."""
    text = retro_path.read_text(errors="replace")
    m = SUMMARY_RE.search(text)
    if not m:
        return retro_path.stem.split("_", 1)[-1].replace("-", " ")
    rest = text[m.end():]
    end_m = NEXT_SECTION_RE.search(rest)
    block = rest[: end_m.start()] if end_m else rest
    block = block.strip()
    # First sentence: cut at the first ". " or ".\n" after some minimum length,
    # falling back to a hard truncate.
    cut = len(block)
    for m2 in re.finditer(r"[.!?](?:\s|$)", block):
        if m2.start() > 20:
            cut = m2.start() + 1
            break
    sentence = block[:cut].strip()
    sentence = MD_STRIP_RE.sub("", sentence).replace("\n", " ")
    sentence = re.sub(r"\s+", " ", sentence)
    if len(sentence) > max_len:
        sentence = sentence[: max_len - 1].rstrip() + "…"
    return sentence or retro_path.stem.split("_", 1)[-1].replace("-", " ")


def collect_done_rows():
    files = sorted(ss.RETRO_DIR.rglob("*.md"))
    rows = []
    for f in files:
        row = ss.classify(f)
        if row["status"] != "DONE":
            continue
        date_key = ss.date_key_from_path(f)
        date = date_key.split(" ")[0]
        sid = row["session_id"] or "?"
        title = summary_title(f)
        rows.append((date, sid, title))
    # newest first
    rows.sort(key=lambda r: r[0], reverse=True)
    return rows


SHORT_ID_RE = re.compile(r"^[0-9a-f]{8}$")


def claude_projects_dir() -> Path:
    # Matches Claude Code's own project-dir encoding: '/', '.', and '_' all become '-'.
    encoded = "-" + re.sub(r"[/._]", "-", str(REPO_ROOT).lstrip("/"))
    return Path.home() / ".claude" / "projects" / encoded


def resolve_full_session_id(short_id: str, report_html: str) -> str:
    """Session retrospectives only store the first 8 hex chars; recover the full UUID
    from the actual session .jsonl filename first (authoritative), falling back to
    report.html's own resume commands (which already carry full UUIDs) if not found."""
    if not SHORT_ID_RE.match(short_id):
        # Not a real short id (e.g. "?" when the retro had no 📡 Session: header) —
        # globbing this would match every file in the dir, so bail out instead.
        return short_id
    proj_dir = claude_projects_dir()
    if proj_dir.is_dir():
        matches = sorted(proj_dir.glob(f"{short_id}*.jsonl"))
        if matches:
            return matches[0].stem
    m = re.search(r"--resume\s+(" + re.escape(short_id) + r"[0-9a-f-]*)", report_html)
    return m.group(1) if m else short_id


def build_howto_section() -> str:
    script_rel = Path(__file__).resolve().relative_to(REPO_ROOT)
    return f'''<details class="howto">
  <summary>⚙️ วิธีรันสคริปต์นี้ใหม่ (อัพเดตข้อมูล)</summary>
  <div class="howto-body">
    <p>1. รวมข้อมูลใหม่จากของที่มีอยู่แล้ว (เร็ว):</p>
    <pre><code>cd {esc(str(REPO_ROOT))}
python3 {esc(str(script_rel))}</code></pre>
    <p>2. หรือ rescan session ทั้งหมดใหม่ก่อนด้วย (ช้ากว่า ~1-2 นาที แต่ข้อมูลสดสุด):</p>
    <pre><code>python3 {esc(str(script_rel))} --refresh-source</code></pre>
    <p>ผลลัพธ์ถูกเขียนที่ <code>ψ/incubate/memory-horizon-cron/dashboard.html</code> (gitignored, ไม่มีทาง commit หลุด) —
    เอาไฟล์นี้ไปให้ Claude publish เป็น Artifact ใหม่ได้เลย (private โดยเริ่มต้น)</p>
  </div>
</details>

'''


def build_done_section(done_rows, report_html: str) -> tuple[str, int]:
    row_html = []
    for date, sid, title in done_rows:
        full_sid = resolve_full_session_id(sid, report_html)
        row_html.append(
            f'<tr><td class="quiet">{esc(date)}</td><td class="title">{esc(title)}</td>'
            f'<td class="src">claude</td><td class="cmd">'
            f'<code onclick="selectText(this)">claude --resume {esc(full_sid)}</code></td></tr>'
        )
    n = len(done_rows)
    plural = "session" if n == 1 else "sessions"
    section = f'''<section id="done">
  <h2><span class="badge done"></span> DONE — {n} {plural}</h2>
  <div class="note">คนละแหล่งข้อมูลกับหมวดด้านล่าง — วัดจาก Self-Audit ในตัว retrospective เอง (blocked: 0, next steps: 0)
  ไม่ใช่วัดจากความเงียบ/เวลา จึงมีแค่ session ที่เขียน `/rrr` retrospective ไว้เท่านั้นถึงจะขึ้นในนี้ได้.</div>
  <input class="filter" type="text" placeholder="พิมพ์เพื่อกรอง..." onkeyup="filterTable(this,'done-table')">
  <div style="overflow-x:auto"><table id="done-table">
    <tr><th>ปิดงานเมื่อ</th><th>เรื่อง</th><th>Source</th><th>Resume</th></tr>
    {chr(10).join(row_html)}
  </table></div>
</section>

'''
    return section, n


class SourceDriftError(RuntimeError):
    """report.html no longer matches the literal text this script depends on."""


def must_replace(src: str, old: str, new: str, label: str, count: int = 1) -> str:
    found = src.count(old)
    if found < count:
        raise SourceDriftError(
            f"expected to find {count}x {label!r} marker in report.html, found {found}. "
            f"memory-horizon-cron's generator likely changed its output — update build_dashboard.py "
            f"to match, don't just re-run."
        )
    return src.replace(old, new, count)


def must_sub(src: str, pattern: str, repl: str, label: str, **kwargs) -> str:
    new_src, n = re.subn(pattern, repl, src, **kwargs)
    if n == 0:
        raise SourceDriftError(
            f"expected regex {label!r} to match at least once in report.html, found 0 matches. "
            f"memory-horizon-cron's generator likely changed its output — update build_dashboard.py "
            f"to match, don't just re-run."
        )
    return new_src


def transform(report_html: str, done_rows) -> str:
    src = report_html

    # 1. Strip outer <!doctype>/<html>/<head>/<body> wrapper -> Artifact-ready fragment.
    src = must_sub(
        src, r"^<!doctype html>\s*\n<html[^>]*>\s*\n<head>\s*\n<meta charset=\"utf-8\">\s*\n", "",
        "doctype/html/head open",
    )
    src = must_replace(src, "</head>\n<body>\n", "", "head-close/body-open")
    src = must_sub(src, r"\n</body>\s*\n</html>\s*$", "", "body-close/html-close")

    # 2. Wrap each data table for horizontal scroll at phone width.
    src = must_sub(
        src,
        r'(<table id="[a-z]+-table">.*?</table>)',
        r'<div style="overflow-x:auto">\1</div>',
        "data table",
        flags=re.DOTALL,
    )

    # 3. Add --done token + stat/badge color rules.
    src = must_replace(
        src,
        "--live:#34d399; --cooling:#fbbf24; --dormant:#94a3b8; --deprecated:#f87171; --lost:#c084fc;",
        "--live:#34d399; --cooling:#fbbf24; --dormant:#94a3b8; --deprecated:#f87171; --lost:#c084fc; --done:#a3e635;",
        "CSS color tokens",
    )
    src = must_replace(
        src,
        "  .stat.lost .n { color:var(--lost); }",
        "  .stat.lost .n { color:var(--lost); }\n  .stat.done .n { color:var(--done); }",
        "stat.lost CSS rule",
    )
    src = must_replace(
        src,
        "  .badge.lost { background:var(--lost); }",
        "  .badge.lost { background:var(--lost); }\n  .badge.done { background:var(--done); }",
        "badge.lost CSS rule",
    )

    # 3b. CSS for the collapsible "how to run" block, appended right before </style>.
    src = must_replace(
        src,
        "</style>",
        '''  details.howto { background:var(--panel); border:1px solid var(--border); border-left:3px solid var(--done);
    border-radius:6px; margin:16px 24px 0; max-width:1132px; }
  details.howto summary { padding:12px 18px; cursor:pointer; font-size:0.85rem; font-weight:600; list-style:none; }
  details.howto summary::-webkit-details-marker { display:none; }
  details.howto[open] summary { border-bottom:1px solid var(--border); }
  .howto-body { padding:4px 18px 16px; font-size:0.83rem; color:var(--muted); }
  .howto-body p { margin:10px 0 4px; }
  .howto-body pre { background:var(--panel2); border:1px solid var(--border); border-radius:6px;
    padding:10px 14px; overflow-x:auto; margin:6px 0; }
  .howto-body code { color:var(--accent); font-size:0.8rem; }
  .howto-body pre code { color:var(--text); }
</style>''',
        "</style> closing tag (for howto CSS append)",
    )

    # 3c. Insert the how-to block between the privacy banner and the header.
    src = must_replace(
        src,
        "</div>\n\n<header>",
        "</div>\n\n" + build_howto_section() + "<header>",
        "privacy-div-close / header-open marker",
    )

    done_section, n_done = build_done_section(done_rows, report_html)

    # 4. Stat card, inserted before the LIVE card.
    src = must_replace(
        src,
        '<div class="stat live" onclick',
        f'<div class="stat done" onclick="location.href=\'#done\'"><div class="n">{n_done}</div>'
        f'<div class="l">Done</div></div>\n    <div class="stat live" onclick',
        "LIVE stat card",
    )

    # 5. Section, inserted before <section id="live">.
    src = must_replace(src, '<section id="live">', done_section + '<section id="live">', "LIVE section marker")

    return src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--refresh-source", action="store_true",
                     help="re-run memory-horizon's own daily-cron.sh first (rescans all sessions, ~1-2 min)")
    args = ap.parse_args()

    if args.refresh_source:
        print(f"Refreshing source via {DAILY_CRON} ...", file=sys.stderr)
        subprocess.run(["bash", str(DAILY_CRON)], check=True)

    if not SOURCE_REPORT.exists():
        print(f"ERROR: {SOURCE_REPORT} not found. Run with --refresh-source first, "
              f"or run daily-cron.sh manually.", file=sys.stderr)
        sys.exit(1)

    report_html = SOURCE_REPORT.read_text(encoding="utf-8")
    done_rows = collect_done_rows()
    merged = transform(report_html, done_rows)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(merged, encoding="utf-8")
    print(f"Wrote {args.output} ({len(merged)} bytes, {len(done_rows)} DONE rows)")
    print("This file is gitignored (ψ/incubate/) and contains real session data — "
          "don't commit it. Hand its path to Claude to publish as a private Artifact.")


if __name__ == "__main__":
    main()
