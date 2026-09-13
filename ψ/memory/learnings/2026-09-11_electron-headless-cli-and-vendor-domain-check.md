---
pattern: Electron-packaged CLIs often run headless via ELECTRON_RUN_AS_NODE=1; verify a vendor download domain against one already used this session before trusting it
date: 2026-09-11
source: rrr: ayami-oracle
concepts: [electron, headless-cli, appimage, domain-verification, supply-chain]
---

# Two small, reusable facts from installing zcode on a headless Linux sandbox

## 1. `ELECTRON_RUN_AS_NODE=1` unlocks headless mode for Electron-bundled CLIs

zcode's official Linux distribution is an Electron AppImage/.deb/.rpm — no separate CLI binary
like the macOS `.app`'s bundled `zcode.cjs`. Assumed this meant it needed a real display (the
target box had no X server, and AppImage's FUSE dependency was also missing). Instead:

```bash
./ZCode-*.AppImage --appimage-extract        # no FUSE needed, unpacks to squashfs-root/
ELECTRON_RUN_AS_NODE=1 ./squashfs-root/zcode ./squashfs-root/resources/glm/zcode.cjs --help
```

worked immediately — the bundled `zcode` binary *is* Electron, and `ELECTRON_RUN_AS_NODE=1` makes
Electron run as a plain Node interpreter against the given script instead of launching its GUI
shell. This is a general Electron behavior (same trick works for VS Code, Cursor, and other
Electron apps that ship a CLI entry point bundled inside the app resources), worth trying before
assuming a GUI-distributed tool is a dead end on a headless box.

## 2. Cross-check a vendor download domain against one already verified this session

A web search for "zcode Linux install" surfaced two candidate download sources: the vendor's own
`zcode.z.ai` (matches `api.z.ai`, already used and trusted earlier in the same session) and
`zcode-z.com` (a different, unverified domain, never referenced anywhere else). Used only the
`z.ai`-matching one; ignored the lookalike entirely rather than trying to adjudicate it on its own
merits.

**How to apply**: when a search result set for "how to install/download X" includes multiple
plausible-looking domains, don't evaluate each in isolation — check whether any of them matches a
domain already established as legitimate earlier in the same session (an API endpoint the user
has been paying/authenticating against, a docs link they've referenced, etc.). A domain that
doesn't match gets skipped by default, not investigated further, unless there's a specific reason
to trust it.
