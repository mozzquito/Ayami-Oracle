---
pattern: When delegating real multi-file implementation to a headless coding-agent CLI (zcode/agy/etc), never trust its own success/failure exit message — diff the actual working tree against a pre-delegation backup before deciding what happened, and kill by finding the real worker process (not just the invocation pattern) before delegating the same target directory to a second agent.
date: 2026-08-18
source: "rrr: ayami-oracle"
concepts: [zcode, agy, cli-agent-reliability, process-management, delegation-safety]
---

# Never trust a CLI coding agent's exit status — diff the tree

While delegating a 6-feature dashboard implementation to `/zcode` and `/agy` (non-interactive
CLI subprocesses), both tools' own reported outcomes turned out to be actively misleading in
opposite directions:

- **zcode** reported `Turn execution failed` on attempt 1 — genuinely nothing changed, that one
  was accurate. But on the retry, the visible wrapper process sat at 0% CPU for 35+ minutes with
  zero file diff, got killed via `pkill -f "zcode -p"`, and was declared dead. It wasn't: a
  **detached worker process** (`zcode-cli`, a different process name entirely) survived that kill
  and kept running invisibly, eventually writing a complete, high-quality multi-client backend
  implementation — discovered only by chance via `ps aux` while investigating something else,
  after I had already started rewriting the same file myself. The Edit/Write tool's stale-file
  guard ("File has been modified since read") blocked my overwrite by luck, not by my own
  vigilance.
- **agy** (`--mode accept-edits`, headless) reported `no output produced — a tool required the
  "command" permission that headless mode cannot prompt for` — sounds like total failure, and the
  final summary was indeed empty. But it had actually completed real partial work (a full data
  migration to a new directory layout) before hitting the permission wall on some later Bash-tool
  step. The one-line error gives zero indication of what, if anything, was written.

**Rule going forward:**
1. `cp -R` a full backup of the target directory before any delegation that grants Edit/Write.
2. After the CLI returns (success OR failure), `diff -rq backup/ target/` before reading its
   summary — the diff is ground truth, the CLI's self-report is not.
3. Before killing a hung/failed CLI invocation and re-delegating to a different tool on the same
   directory, verify with `ps aux` that the actual worker process (not just the `<tool> -p ...`
   wrapper pattern) is gone. These CLIs commonly spawn differently-named child/worker processes
   that outlive a `pkill` targeted at the wrapper's command line.
4. Never fire two agents at the same target directory without confirming #3 first — a leftover
   writer plus a new writer on the same files is a real corruption risk, not a theoretical one.

This generalizes beyond this specific pair of tools: any headless, non-interactive agent CLI
invoked via subprocess should be treated as a **black box whose exit status is advisory at best**.
The filesystem is the only reliable source of truth for what it actually did.
