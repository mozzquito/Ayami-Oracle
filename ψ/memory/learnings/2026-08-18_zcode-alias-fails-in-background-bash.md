---
pattern: "zcode is a shell alias, not a PATH binary — it does not resolve inside run_in_background Bash calls, only in foreground calls; use the underlying node path directly for background delegations"
date: 2026-08-18
source: "rrr: ayami-oracle (drivedb)"
concepts: [zcode, run_in_background, shell-aliases, tooling]
---

# zcode alias fails silently in background Bash calls

`zcode` is defined in `~/.zshrc` as a shell alias:

```
alias zcode="node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs"
```

It is not a real binary on `PATH` — `which zcode` and `type zcode` both report
"not found." It has worked correctly throughout this project via foreground
Bash calls because those calls source a shell snapshot
(`~/.claude/shell-snapshots/snapshot-zsh-*.sh`) before running, which picks up
`.zshrc`'s aliases.

**`run_in_background: true` Bash calls do not go through the same sourcing
path.** Launching `zcode -p "..." --cwd ...` in the background fails
immediately with `command not found: zcode` (exit 127) — a fast, clear
failure, not a hang, so it's easy to catch, but it still costs a full
launch-diagnose-relaunch round-trip every time it's hit fresh.

**Fix**: when delegating to zcode from a background Bash call specifically,
skip the alias and call the underlying command directly:

```bash
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs -p "<prompt>" --cwd "<path>" ...
```

This is a drop-in replacement — same flags, same behavior — since the alias
is nothing more than that `node` invocation.

**Broader rule**: before relying on any shell alias (not a real `PATH`
binary) inside a `run_in_background` call, check whether it's actually an
alias (`type <name>`) and resolve it to the real underlying command first.
Foreground Bash calls in this environment tolerate aliases; background ones
don't. `agy`, by contrast, is a real installed binary at `~/.local/bin/agy`
and works fine in both foreground and background calls without this issue —
this is specific to alias-defined tools, not a general zcode/agy asymmetry.

Worth fixing at the source eventually: either update the `/zcode` skill's
documented non-interactive invocation to use the direct `node` path instead
of the alias (removing the failure mode entirely, since the direct path also
works fine in foreground calls), or note this constraint prominently in the
skill so it's not re-diagnosed from scratch on the next background
delegation.
