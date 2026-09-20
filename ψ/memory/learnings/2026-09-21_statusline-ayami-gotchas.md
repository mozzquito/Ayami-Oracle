# statusline-ayami: what bit us (2026-09-21)

Work: `.claude/scripts/statusline-ayami.sh`, design + tests in `ψ/lab/statusline/` (commit ce7ebd4d).

1. **A cache that only writes on success turns failure into a retry storm.** If the refresh fails and leaves no file, every render re-spawns the slow command. On failure: `touch` the old file (keep last good value) or create an empty marker, so the TTL rate-limits retries. Both zcode and agy found this independently.
2. **`alarm` + `exec` kills only the direct child.** `npx` -> `node` grandchildren kept the pipe open and the "timeout" did nothing. Run the command in its own process group (`setpgrp`) and kill `-$pid`. macOS has no `timeout`; perl does the job.
3. **macOS bash is 3.2.** No `$EPOCHSECONDS` (agy's advice was wrong here: verify reviewer claims on the real machine), no `${x,,}`, and `{a,b}` inside quotes nested in `"$( )"` gets brace-expanded wrongly (tests: use a flat helper).
4. **Test hygiene:** a `pgrep -f "<literal>"` also matches the shell whose command line quotes the test source, so build markers at run time. Redo any "clean" scan whose file list never expanded (`$FILES` is not word-split in zsh: pass files as real arguments).
5. **Verify the input schema against real data, not only the docs.** A debug dump (`touch .tmp/statusline/debug`) of live stdin confirmed the fields and revealed `prompt_cache` (cold cache = next turn re-writes the whole context at full price), which drove a feature.
6. Stale-looking state misleads: a focus file untouched for 12 h is shown as 💤, not as the current task.
7. Two live sessions share `AGENT_ID=main` and overwrite each other's `ψ/inbox/focus-agent-main.md` (seen at 04:27). Not fixed here.
