---
pattern: "Scale verification effort to the actual risk surface of a change — don't apply the same ceremony to a read-only feature and a security-critical hardening change"
date: 2026-08-08
source: "rrr: ayami-oracle"
concepts: ["verification", "judgment", "proportionality"]
---

# Match verification effort to actual risk

Two changes in the same session, verified differently on purpose:

1. A hardening rewrite of `.claude/hooks/safety-check.sh` (blocks dangerous shell commands) got an explicit 19+ case test suite plus a simulated multi-agent-worktree setup before being trusted — because it's security-critical and a delegated agent's prior "fixed" claim on the same file had turned out to disable the primary protection entirely.
2. A "สรุปงาน" (work summary) feature added to a Discord bot — read-only, summarizes an in-memory array, no file writes, no security surface — got a live functional test via the human's actual Discord client and nothing more.

Both were the right amount of verification for their respective risk. Treating every change with the security-hook level of ceremony would waste time on low-risk features; treating every change with the summary-feature's light-touch verification would risk the exact regression found earlier in the same session.

**Rule**: before verifying a change, ask what's actually at stake if it's silently wrong — data loss, a security bypass, a broken safety net vs. a slightly-off chat reply. Let that answer set the verification bar, rather than defaulting to either "always exhaustive" or "always light."

Secondary note: before attempting an API action on behalf of a service credential (a bot token, etc.), check what permissions it actually has rather than attempting the call and reacting to failure — and weigh whether re-granting permissions is actually cheaper than just asking the human to do the one manual step, especially if the auth flow to grant more permissions was itself painful earlier in the session.
