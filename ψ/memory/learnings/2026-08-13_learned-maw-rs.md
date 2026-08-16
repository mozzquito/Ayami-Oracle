---
pattern: "Learned maw-rs: Rust rewrite of maw-js, 13-crate Cargo workspace, still dual-maintenance/partial parity (81/135 verbs native). Deliberately NOT installed — its installer would silently shadow the working maw-js on PATH (~/.local/bin precedes ~/.bun/bin)."
date: 2026-08-13
source: "learn: Soul-Brews-Studio/maw-rs"
concepts: ["learn", "codebase", "maw", "rust", "tmux", "multi-agent", "orchestration", "cargo-workspace"]
---

# Learned maw-rs

- Rust port of maw-js. 13-crate Cargo workspace layered pure→impure: leaf crates (`maw-matcher`, `maw-worktree`, `maw-auth`, `maw-xdg`) are side-effect-free; mid crates (`maw-tmux`, `maw-transport`, `maw-peer`, `maw-schedule*`, `maw-discord`) add controlled I/O; `maw-cli` is the top-level binary (~229 per-command dispatcher files in `core_impl/`). Tokio async runtime, Axum for HTTP/WS, `forbid(unsafe_code)`, clippy-pedantic as CI errors. Every ported module is validated against JSON fixtures captured from maw-js for behavioral parity.
- **Not feature-complete**: parity tracker shows 81/135 verbs native, 29 WASM, 13 stubbed, 12 not yet ported — currently Phase 1 of a 3-phase roadmap (core crates + native commands → transports/discovery → full parity). Not a safe swap-in replacement for maw-js yet.
- On this machine, deliberately left uninstalled: [[2026-08-13_learned-maw-js|maw-js]] is already installed and current (`v26.5.21` @ `~/.bun/bin/maw`) and is what this project's CLAUDE.md `maw peek`/`maw sync`/`maw hey` commands run against. maw-rs's installer defaults to `~/.local/bin/maw`, and since `~/.local/bin` precedes `~/.bun/bin` in this user's `PATH`, installing it would have silently taken over the `maw` command. Asked the user first; they chose docs-only over install.
