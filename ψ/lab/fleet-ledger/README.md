# fleet-ledger (experiment, local only, not wired into any hook or skill)

Append-only log of what Ayami (Claude) sent to `/zcode`, `/agy`, `/grok` and Grok Bot, whether an answer came back, how long it took, and how many of the
reply's claims turned out wrong when Ayami checked them. Answers "what did I send that has not come back?" and slowly builds data on which agent over-claims.
Design and review trail: `REQUIREMENTS.md`, `DESIGN.md`. Idea #1 from the Soul-Brews-Studio research (2026-09-21).

Stores label + SHA-256 + length only. Never the prompt, never the reply. Ledger: `ψ/memory/logs/fleet-ledger.jsonl` (git-ignored, mode 0600).
Labels are typed by Ayami: keep them short and free of secrets/PII (limit 200 characters). Never used for eVisa/Wayama work content.

```bash
F=ψ/lab/fleet-ledger/fleet.py           # stdlib only, python3 >= 3.9. Call it directly (not through `uv run`) so signals reach it.

# CLI agents: wrapper records sent + done itself, works in the background, output/exit code pass through unchanged
$F run --agent zcode --label "review requirements" -- zcode -p "…" --cwd "$PWD" --disallowedTools "Edit Write Bash"
$F run --agent agy   --label "wrapper review" --timeout 900 -- agy -p "…" --mode plan

# Grok Bot (MCP) is logged by hand:
ID=$($F log sent --agent grokbot --label "ask Grok: exit rule" --prompt-file p.txt)   # then use $ID as messageId in grokbot_send
$F log done --id "$ID" --status ok --duration-s 1500                                # when the reply is read
$F log checked --id "$ID" --total 7 --wrong 1 --note "one wrong API shape"          # after Ayami verified the reply against source
$F abandon "$ID" --reason "never answered"

$F pending          # sent with no done/abandoned; older than 12 h is marked STALE (read-time only)
$F recent 10
uv run --no-project --with pytest pytest -q      # tests (offline)
```

Things to know
- `zcode` in a `run` command is replaced by `node /Applications/ZCode.app/…/zcode.cjs` (the shell alias does not exist in background Bash).
- `access` (read-only/write/unknown) is guessed from the flags and is advisory. `output_len` is only measured when stdout is a seekable file (e.g. `> out.txt`), else null.
- Ledger write problems never stop a `run` (it warns and runs the command); explicit `log`/`abandon` calls fail loudly (exit 2).
- flock is advisory: a human `>>` bypasses it. The reader skips and counts malformed lines, and the next write starts on a fresh line.
- Hand-logging Grok Bot is easy to forget; a forgotten `sent` is invisible. Nothing enforces it yet.
- Not done on purpose: cost tracking, automatic hooks, Jev calls (jev-gate has its own shadow.jsonl), Discord `squad status`.
