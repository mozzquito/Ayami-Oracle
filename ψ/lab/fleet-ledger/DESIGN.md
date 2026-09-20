# fleet-ledger — design (v2, after review by zcode + agy, 2026-09-21)

Requirements: `REQUIREMENTS.md` (v2 + the v2.1 section at the bottom). Decisions validated by Moss: wrapper `fleet run` + hand-logging for
Grok Bot; keep `checked`; store label + hash + length only; Jev out of scope.

## Layout
`ψ/lab/fleet-ledger/fleet.py` (single file, stdlib only, Python ≥ 3.9), `test_fleet.py`, `README.md`.
Ledger: `ψ/memory/logs/fleet-ledger.jsonl` (git-ignored through `ψ/.gitignore` → `memory/logs/`), created mode 0600; override with env `FLEET_LEDGER`.
Nothing under `.claude/` is touched.

## Format
One JSONL file. Every line: `{"v":1,"ev":…,"ts":…,"id":…, …fields}`; `ev` ∈ sent | done | abandoned | checked; `ts` is timezone-aware ISO-8601 (local offset).
- sent: agent, label, prompt_sha256, prompt_len, access (any of these may be null except agent/label/access)
- done: status (ok|error|timeout), exit, duration_s, output_len (all but status nullable)
- abandoned: reason
- checked: claims_total, claims_wrong, note
`prompt_sha256` = SHA-256 of the UTF-8 prompt text, `prompt_len` = characters.
Chosen over one-file-per-event (agy's proposal): greppable, same pattern as shadow.jsonl / activity.log; per-event files would need pending→done moves
that look like deletion. Reopen only if test A3 shows corruption.

## Write path — `append_event(event, validate=True)`
1. Serialize one line (compact, ensure_ascii=False); reject if > 4096 bytes (backstop; bounded fields make ~500 B typical).
2. `os.open(O_WRONLY|O_APPEND|O_CREAT, 0o600)`, then `flock(LOCK_EX|LOCK_NB)` retried for up to LOCK_WAIT_S (5 s) → else LedgerBusy.
3. Under the lock: (a) if the file is non-empty and its last byte is not `\n` (a hand-appended, truncated line), prepend `\n` so the fragment stays its own line;
   (b) if `validate`, read the file through a separate read-only descriptor and apply the state rules; (c) write in a loop until all bytes are written.
4. Close (releases the lock). flock is advisory: a human `>>` bypasses it — the tolerant reader is the defense there, not the lock.
State rules (explicit commands): `sent` id unique; other events need a known id; second `done`, `done` after `abandoned`, `abandoned` after `done` rejected; `checked` allowed always.

## Read path
`read_events` skips and counts malformed lines (bad JSON, not an object, missing v/ev/id/ts or required fields, naive timestamp). `fold` groups by id (first `sent` and first
terminal event win; hand-made duplicates are ignored). pending = sent without done/abandoned; `stale` = pending older than `--stale-hours` (12), computed at read time only.
Readers print `warning: N malformed line(s) skipped` to stderr and exit 0.

## Commands
```
fleet run --agent zcode|agy|grok-cli --label TEXT [--id UUID] [--access read-only|write|unknown] [--timeout SEC] -- COMMAND…
fleet log sent    --agent zcode|agy|grok-cli|grokbot --label TEXT [--id UUID] [--prompt-file PATH|-] [--access A]   # prints only the id
fleet log done    --id UUID --status ok|error|timeout [--exit N] [--duration-s S] [--output-len N]
fleet log checked --id UUID --total N --wrong M [--note TEXT]
fleet abandon UUID --reason TEXT
fleet pending [--stale-hours H]        fleet recent [N]
```
Grok Bot sequence: `ID=$(fleet log sent --agent grokbot --label "…" --prompt-file p.txt)` → use `$ID` as `messageId` in `grokbot_send` → `fleet log done --id $ID --status ok` when the reply is read.

## `fleet run`
- `zcode` as argv[0] becomes two argv elements `node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs` (no alias outside an interactive shell).
- Prompt for hash/len and `access` come from a tiny non-abbreviating argparse over the child argv: `-p/--prompt/--print`, `--disallowedTools`, `--mode`, `--yolo`,
  `--dangerously-skip-permissions`; if no prompt is found the joined argv is hashed. read-only ⇐ `--mode plan` or Edit+Write both disallowed; write ⇐ `--yolo`/skip-permissions/`--mode accept-edits`;
  else unknown. Advisory only; `--access` overrides.
- The child inherits stdin/stdout/stderr (no piping: keeps ordering, colors and buffering identical). `output_len` = movement of the shared stdout file offset, only when stdout is a seekable file, else null.
- Order: write `sent` → launch → wait → write `done`. If `sent` cannot be written (busy/IO) warn, run anyway, skip `done`. Duplicate user-supplied `--id` aborts before launch (exit 2).
  If the command cannot start: `done` status error, exit 127 (not found) / 126, then exit with that code. Wrapper exit code = child's exit code (128+N for death by signal N; 124 on timeout).
- SIGTERM is forwarded to the child. SIGINT is forwarded only with `--timeout` (child in its own session); otherwise the terminal already sent it to the whole foreground group.
- `--timeout`: child started in a new session (stdin becomes /dev/null if the wrapper's stdin is a TTY); on expiry SIGTERM to the group, SIGKILL after 5 s; status timeout, exit 124.
- SIGKILL of the wrapper cannot be handled: the event stays pending and turns `stale`.

## Test plan (test_fleet.py, pytest, FLEET_LEDGER in a tmp dir)
A1 background run (fake sleeping command, duration within ±5 s; real zcode pong is a manual acceptance run) · A2/A7/A9 state rules, abandon, checked · A3 5 procs × 50 events, each worker opens its own fd, plus once with validation on ·
A4 truncated tail: reader warns via both `recent` and `pending`, exit 0, and the NEXT append is not swallowed · A6 label > 200 chars rejected; a fake secret in the prompt never reaches the file ·
A8 stdout/stderr/exit 3 identical through the wrapper; ledger records error/3 · extras: launch failure, `--timeout`, SIGTERM forwarding, LedgerBusy fail-open, missing `ev` = malformed, zcode/access/prompt extraction units. A5 by `git status`.

## Residual risks (stated, not solved)
Hand-logging Grok Bot is easy to forget (a forgotten `sent` is invisible). The state-rule scan reads the whole file (fine to thousands of events). `access` can be wrong. Grandchildren of a child can outlive a plain SIGTERM without `--timeout`.

## Second pass (2026-09-21) — decisions, from the zcode + agy reviews (outputs in .tmp/fleet-ledger/ and .tmp/fanout/)
- Task board replaced by an optional `group` field (agy: one store; zcode had ranked the board last and warned it rots). `OPTIONAL_TYPES` are validated only when present.
- Grok Bot auto-log: hook script + PreToolUse (see README for the trade-off). The hook reads its own stdin, passes the prompt to `fleet log sent --prompt-file -` through a pipe, exits 0 always, label fixed. A duplicate messageId (re-send to inspect) is a quiet no-op that says the first hash is kept.
- fanout: parallel `fleet run` wrappers, own files per agent, `--yes-public` required and not abbreviable, brief path relative to `--cwd`, no overwrite, SIGTERM/Ctrl-C terminates the wrappers (each forwards to its agent and still writes `done`).
- Rejected review claims: agy said `--mode plan` forces a plan artifact (contradicted: every run with the stdout instruction returned text on stdout, incl. this one); agy said Ctrl-C leaves agents running (only true for a plain SIGTERM, fixed).
