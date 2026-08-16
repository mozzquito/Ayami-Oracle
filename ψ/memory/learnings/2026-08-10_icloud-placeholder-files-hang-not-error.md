---
pattern: "Files under ~/Documents or ~/Desktop that hang or error strangely on read (unzip \"end-of-central-directory not found\", `file` hanging) may be un-synced iCloud Drive placeholders, not corrupt files"
date: 2026-08-10
source: "rrr: ayami-oracle"
concepts: [icloud, macos, debugging, file-access, root-cause]
---

# iCloud placeholder files hang or error strangely — check `bird`, not the file

## What happened

Tried to `unzip` a `.pptx` under `~/Documents/EVISA/...` to extract text. First attempt hung
until the tool timed out. Retried with stdin redirected to `/dev/null` — got a fast, confident
"End-of-central-directory signature not found... cannot find zipfile directory," which reads
like a genuinely corrupt file. `ls -la` reported the correct file size the whole time.

Root cause, found by checking `ps aux | grep bird`: `/System/Library/PrivateFrameworks/
iCloudDriveCore.framework/.../bird` was actively running and using CPU — the file was an
iCloud Drive placeholder (metadata present locally, content not yet downloaded / "Optimize
Mac Storage" evicted it), and macOS was materializing it on first real read. Even basic
`file`, `stat`+`wc -c`, `ls -la@` calls stalled for 30–120+ seconds during this.

## Why

`ls -la` size comes from filesystem metadata, which iCloud Drive keeps accurate for
placeholders even when the actual bytes aren't local yet. Tools that do a real content read
(`unzip`, `file`, `tail -c`) trigger on-demand download via `bird`, which can take anywhere
from instant to minutes depending on file size and sync backlog — and some tools report a
misleading "corrupt file" error if they read a stub before the download completes rather than
blocking cleanly.

## How to apply

- If a file read hangs or throws a confusing "not a valid X" / "corrupt" error on a file in
  an iCloud-synced location (`~/Documents`, `~/Desktop` are the common ones with "Desktop &
  Documents" sync enabled), check `ps aux | grep bird` before assuming the file is bad.
- Don't conclude "file is corrupt" from a fast, confident-looking parser error alone if the
  path is cloud-synced — a genuinely corrupt file and a mid-download placeholder can look
  identical to `unzip`/`file`.
- Fix is to wait for `bird` to finish (or trigger materialization explicitly, e.g. open the
  file once in Finder/Preview) — not to re-download or recreate the file.
