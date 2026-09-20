---
pattern: On macOS without pandoc, read docx via `textutil -convert txt -stdout`, edit/insert into docx via `uv run --with python-docx python3 script.py` (no global env pollution); always list paragraph indices before scripting inserts, and verify by re-converting to text before handing off
date: 2026-09-14
source: rrr: ayami-oracle
concepts: [docx, textutil, python-docx, uv, document-editing, tor-compliance]
---

# Editing .docx files ad-hoc without pandoc

**Context**: Asked to compare a Microsoft 365 datasheet (.docx) against a TOR requirement (photographed spec) and then annotate ("remark") the datasheet in place with compliance notes.

**What worked**:
- No `pandoc` on this machine. `textutil -convert txt -stdout <file>.docx` (macOS built-in) is a reliable zero-install way to read docx content into plain text for analysis.
- For writing/editing, `uv run --with python-docx python3 script.py` installs python-docx into an ephemeral env for that one run — no need to touch the global Python or the project's own dependencies.
- Before scripting any `insert_paragraph_before`/anchor-based edit, first dump `enumerate(doc.paragraphs)` with index + style + text preview. python-docx has no "insert after" primitive — you insert before the *next* paragraph, so you need exact anchor indices, and table content doesn't show up in `doc.paragraphs` (tables are separate).
- After the edit script runs, re-convert the output docx back to text with `textutil` and read it before telling the user the job is done — don't trust the script's exit code alone as proof of correct placement.

**Gotcha**: writing a temp script to bare `/tmp/...` failed with "read-only file system" under this session's sandbox. Use the scratchpad directory named in the system prompt instead — it's writable and session-scoped.

**Open question not resolved this session**: when a "remark" request is for a document that may be forwarded to a third party (not just an internal draft), it's worth asking upfront whether they want real Word track-changes/comments vs. plain inline colored text — this session picked inline text unprompted and the user didn't object, but for higher-stakes documents that choice belongs to the user.
