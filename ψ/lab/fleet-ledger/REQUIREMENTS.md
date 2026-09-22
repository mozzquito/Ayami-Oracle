# fleet-ledger — requirements v2 (stage 1, after zcode + agy review, 2026-09-21)

Supersedes REQUIREMENTS-draft.md (kept). Changes from v1 are marked [v2].

## Problem
Ayami (Claude) drives separate agents: `/zcode`, `/agy`, `/grok` (grok-cli), Grok Bot (remote, MCP `mcp__grokbot__*`). Nothing records what
was sent to whom, whether it came back, how long it took, or whether the answer held up. Pain: a Grok Bot message sat `reply_pending`
20+ minutes with no way to ask "what has not come back?". "Reviewers over-claim" is a working rule with no data behind it.

## Facts checked (2026-09-21)
- `ψ/memory/logs/` is gitignored (`git check-ignore` → ψ/.gitignore:2). Only existing per-task log there is `activity.log` (free text).
- `.claude/settings.json` has Bash/Task/Read hooks (safety-check.sh, token-check.sh, log-task-*.sh); none logs zcode/agy/grok/grokbot.
- `grokbot_send` needs a caller-chosen uuid `messageId` (reuse it to inspect an uncertain send) → usable as the ledger id.
- zcode must be launched as `node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs` outside an interactive shell (alias fails); agy, grok are real binaries.
- [v2 fix] `ψ/lab/jev-gate/shadow.jsonl` stores hash + length + verdict PLUS short previews of flagged chunks (gate.py:164-166). Never full text. The ledger will not store previews.
- UNVERIFIED and now irrelevant to the design: whether PostToolUse fires at launch or at finish of a background Bash. Both reviewers doubt hooks can see completion; the chosen design does not depend on it.

## Must-have
M1. Append-only JSONL `ψ/memory/logs/fleet-ledger.jsonl` (gitignored, local only). Corrections are new lines; nothing edited or deleted.
M2. Events linked by `id` [v2 tightened]:
    - `sent`: v, ts, id, agent (zcode|agy|grok-cli|grokbot), label (≤200 chars, written by Ayami, no secrets/PII), prompt_sha256, prompt_len, access
    - `done`: v, ts, id, status (ok|error|timeout), exit, duration_s, output_len
    - `abandoned`: v, ts, id, reason — written only by an explicit `fleet abandon <id>`
    - `checked`: v, ts, id, claims_total, claims_wrong, note
    Rules: id is a uuid4 (grokbot: its messageId); a duplicate `sent` id is rejected; `done`/`abandoned`/`checked` on an unknown id is an error;
    `ts` is timezone-aware ISO-8601 on every event; `access` is set from the flags actually passed (--disallowedTools / --mode plan ⇒ read-only;
    --yolo / accept-edits ⇒ write; otherwise unknown) and is advisory only.
M3. No full prompt or reply text, no previews. Hash + length + label only.
M4. Local CLI `fleet` (Python via `uv`, in `ψ/lab/fleet-ledger/`): `fleet pending`, `fleet recent [N]`, `fleet log sent|done|checked`, `fleet abandon <id>`.
    Readers tolerate a truncated/garbled line: print `warning: N malformed line(s) skipped` on stderr, exit 0.
    `fleet pending` marks a sent event older than 12 h (tunable) as `stale` at read time and never modifies the file.
M5. [v2] `fleet run --agent <a> --label <l> -- <command…>` wraps a CLI agent: writes `sent`, runs the command, writes `done` itself (exit, duration_s,
    output_len), passes stdout/stderr/exit code through unchanged, works when launched in the background, resolves zcode to the absolute node path
    (no alias). No hook dependency. Grok Bot (MCP) is logged by hand with `fleet log`.
M6. [v2] Each event is one line written with a single `os.write` on an `O_APPEND` fd, under `fcntl.flock`; lines kept short. Correctness is proven by test A3, not by assumption.
M7. No change to `.claude/settings*.json` or existing hooks in this pass.

## Nice-to-have (later)
N1 `fleet stats` (per-agent counts, median duration, claims_wrong rate). N2 Discord `squad status`. N3 backfill the known stuck Grok Bot message.
N4 token/cost numbers if a CLI prints them. N5 rotate the file if it passes ~5 MB (not needed yet: one event is a few hundred bytes).

## Non-goals
Money/cost tracking; automatic hooks; other agents writing; instrumenting Grok Bot's remote side; replacing activity.log; storing reply text;
shared task board; Jev calls (jev-gate keeps its own shadow.jsonl) [v2].

## Acceptance checks [v2 rewritten]
A1. `fleet run` around `node …/zcode.cjs -p 'reply pong'`, launched in the background: sent then done, exit 0, duration_s within ±5 s of wall time.
A2. Grok-style send (fresh uuid, no done): listed by `fleet pending`; after `done` it no longer is; `fleet abandon` removes it from pending and is itself logged.
A3. 5 parallel writers × 50 events → exactly 250 valid JSON lines, all ids unique.
A4. Hand-append a truncated line: `fleet recent`/`fleet pending` still work, stderr warns with the count, exit 0.
A5. `git status` shows no change to `.claude/settings*.json`; the ledger file is git-ignored.
A6. Run a prompt containing a fake secret: the ledger contains neither the prompt text nor the secret; an over-long label is rejected/truncated at 200.
A7. `checked` on an existing id shows up joined to its sent/done in `fleet recent`; on an unknown id it errors.
A8. `fleet run` around a fake command that prints to stdout and stderr and exits 3: caller sees identical output and exit 3; the ledger records status error, exit 3.
A9. Duplicate `sent` id is rejected; `done` on an unknown id errors.

## Left for stage 2 (design), not decided here
- Single JSONL file vs one file per event (agy's suggestion: removes append races and truncation, but loses easy grep/jq and the precedent of shadow.jsonl / activity.log).
- Exact CLI syntax; where the wrapper's captured output goes.
- How to make hand-logging of Grok Bot sends hard to forget (residual risk: a forgotten `sent` is invisible).

## Reviewer claims I did NOT accept (checked against source)
- agy: "appends are atomic if smaller than PIPE_BUF" — PIPE_BUF is a pipe guarantee, not a regular-file one. Requirement M6 uses O_APPEND + single write + flock and A3 tests it.
- agy: "Python open('a') buffering will split short writes" — overstated for short lines; single os.write avoids the question anyway.
- zcode: rotation at 10 MB — deferred to N5.

---
## v2.1 changes (after the design review by zcode + agy, 2026-09-21)
- Every line has a discriminator `ev` in {sent, done, abandoned, checked} plus `v`, `ts`, `id`. A line without them is malformed.
- State rules for explicit commands: `sent` id unique; `done`/`abandoned`/`checked` need a known id; a second `done`, `done` after `abandoned`, or `abandoned` after `done` is rejected; `checked` is allowed in any state and may repeat.
- `fleet run`: a user-supplied `--id` is validated and a duplicate aborts before launch; failure to write `sent` (busy/IO) warns and continues, and then `done` is skipped; if the command cannot be started, `done` (status error, exit 127/126) is still written.
- `output_len` is measured only when the wrapper's stdout is a seekable file; otherwise it is null. stdout/stderr are inherited, not piped.
- Units: label and note limits are characters (str length), not bytes. A label over 200 characters is rejected (A6 says rejected, never truncated).
- A4 covers both `fleet recent` and `fleet pending`; a hand-appended line with no trailing newline must not swallow the next event.
- Extra tests: SIGTERM forwarding, --timeout, LedgerBusy fail-open, abandon visible in recent, launch failure.
