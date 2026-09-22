---
pattern: "Learned jaturapornchai/ZCode: open-source Zhipu AI (z.ai/GLM) Claude-Code-style agent — installable on macOS via mise+pnpm, no malicious upload found, but distinct from the ZCode.app desktop binary already flagged in project_zcode_silent_upload_check.md"
date: 2026-09-22
source: "learn: jaturapornchai/ZCode"
concepts: ["learn", "codebase", "zcode", "coding-agent", "supply-chain-review"]
---

# Learned jaturapornchai/ZCode

- This GitHub repo (`jaturapornchai/ZCode`) is a fork/build of Zhipu AI's (z.ai/GLM) open-source
  Claude-Code-style coding agent: Electron desktop app + web UI + CLI/TUI, pnpm monorepo (Node
  24.14.0 pinned via mise, pnpm 10.33.2), Apache-2.0 licensed. `pnpm bootstrap` then `pnpm
  dev:desktop` / `pnpm dev:web` / `pnpm --filter @zcode/cli dev` to run it. No API key needed
  just to start; keys only required once you point an agent at a real LLM provider (20+ providers
  supported).
- Three independent reviews (Claude sub-agents reading source, `/zcode`, and Claude's own read of
  NOTICE.md) found no hidden/silent file-upload path. Disclosed risk surface in NOTICE.md: it can
  transparently redirect Anthropic-compatible API calls through a "ZCode gateway"
  (`ZCODE_BASE_URL`-configurable), bundles Alibaba Cloud ARMS telemetry in the desktop build
  (opt-in/configurable, not hardcoded), stores credentials in locally-encrypted files (not OS
  Keychain), and defaults the `--prompt` CLI mode to "yolo" (no per-step confirmation).
- **This is a different codebase from the earlier concern** in `project_zcode_silent_upload_check.md`
  (ZCode.app 3.6.5 desktop binary already installed on this machine, found to have silent
  workspace-upload code as of 2026-09-19). That finding does not transfer here — don't assume this
  repo is "the same ZCode already checked."
- `/jev` could not run live during this review — no `TYPESAFE_API_KEY` persisted on disk (only
  pasted into chat during the 2026-09-20 trial per `project_typesafe_jev_trial.md`, and that key
  still needs revoking). Skipped rather than searched for a credential.
