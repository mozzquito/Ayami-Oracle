---
pattern: "zcode -p fails with 'Turn execution failed' whenever the prompt requires it to actually read a file — pure-reasoning prompts (no file access needed) succeed fine"
date: 2026-08-31
source: "session: my-template design review delegation"
concepts: ["zcode", "cli-agent", "tool-failure", "delegation"]
---

# zcode fails on any prompt requiring file read, not just Unicode paths

While delegating a design-review task to zcode (`/zcode`), every prompt that required
zcode to open and read a real file failed with `Error: Turn execution failed
(traceId: ...)`, exit code 1 — reproduced 4 times across different variations:

- Real path with a Unicode (ψ) directory component + Thai text in the prompt → failed
- Real path with Unicode directory component, English-only prompt → failed
- File copied to a plain-ASCII scratch path, `--disallowedTools "Edit Write"` → failed
- Same ASCII scratch path, no `--disallowedTools` flag at all → failed

A prompt pointing at a **non-existent** path (typo'd `psi` instead of the real `ψ`
character) *succeeded* — but zcode answered from the description already in the prompt
text, not from actually reading a file (never invoked a read tool).

**Conclusion**: the failure isn't about Unicode paths, `--disallowedTools`, or `--cwd`
placement — it's specifically zcode's file-read tool path erroring out mid-turn in this
environment at this time. `zcode -p "reply with one word: pong"` (no file access) works
fine, confirming the CLI itself is reachable and authenticated.

**How to apply**: if a delegated zcode task needs to read project files and fails with
this exact error, don't keep varying the path/flags — that's not the variable. Either
retry later (could be transient), or paste the file content inline in the prompt instead
of asking zcode to read it, or fall back to `/agy` for that review. Don't burn more than
1-2 retries chasing this specific error before switching approach.
