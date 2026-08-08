---
pattern: "Before telling the user a service/tool is ready to use, check its actual readiness state (build artifacts, install markers) — a process starting cleanly is not the same claim as the feature being usable"
date: 2026-08-08
source: "rrr: ayami-oracle"
concepts: ["agent-decision-error", "cli-tools", "verification"]
---

# Check readiness before declaring a service ready

Ran `maw serve` and `maw ui` back-to-back and told the user to try opening the UI — without checking whether the UI's dist/build actually existed. It didn't; the user hit "maw-ui is not installed or has not been built yet" and had to paste the error back.

The plugin's source (`impl-render.ts`) had already been read in-session and clearly showed an `isUiDistInstalled()` check and an `install` subcommand — the information needed to verify readiness was already in hand and simply wasn't checked before declaring success.

**Rule**: for any `serve`/`start`/`run` command on a tool with a separate build/install step, check the tool's own readiness signal (status command, install marker, dist folder) before telling the user it's ready — "the process started without crashing" and "the feature works" are different claims.
