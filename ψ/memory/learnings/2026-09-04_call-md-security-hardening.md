---
pattern: "Re-learned call.md: security hardening (safeStorage credential encryption, sandboxed renderer, loopback-only server), SSRF-safe webhook validation with DNS pinning, and onboarding session recovery"
date: 2026-09-04
source: learn: video-db/call.md
concepts: ["learn", "codebase", "electron", "security-hardening", "ssrf-prevention"]
---

# Learned call.md (re-run, 2026-09-04)

First learned 2026-08-10; repo advanced ~5 commits (`0e0138c` → `ba53ebe`) since then.

- Security hardening pass: Electron sandbox + context isolation enforced, plaintext credentials
  auto-migrated to OS-backed encryption (`safeStorage`) on startup, sensitive files locked to
  `0600`/`0700`, tRPC/Hono server bound to `127.0.0.1` with CORS restricted to loopback/`file://`.
- SSRF prevention for webhook URLs: DNS lookup + private/reserved IP blocking + DNS pinning to
  close the TOCTOU gap between validation and the actual outbound request.
- Onboarding recoverability: new session-recovery service detects recordings stuck in
  `processing` on startup and recovers them from VideoDB — replaces the removed
  "capture artifact staging helper".
