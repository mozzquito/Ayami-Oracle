---
pattern: "Grep for secret-shaped keys (token|key|secret|authorization|bearer|jwt|password) before doing a full read of any unfamiliar app's config/state file — don't discover the secret mid-dump"
date: 2026-08-22
source: "rrr: ayami-oracle"
concepts: ["security", "credential-handling", "local-machine-audit", "self-correction"]
---

# Grep for secrets before full config read

While auditing a locally-installed third-party AI agent app (AutoClaw) for the user, I ran a Python one-liner that pretty-printed the *entire* contents of its config file (`openclaw.json`) into my own context to understand its shape. That file turned out to contain a live plaintext bearer JWT for the user's account. I caught it mid-read, stopped, avoided repeating the token afterward, and scoped a delegated security review (zcode/agy) away from that file entirely with an explicit exclusion list — but the token had already landed in a tool-output block that's now part of the session transcript by the time I noticed.

The safer sequencing: before the first full read of any unfamiliar app's config, state, or data file, grep for sensitive key names first (`token|key|secret|authorization|bearer|jwt|password`, case-insensitive) — only fall through to a full dump once that comes back clean. This costs nothing when the file is boring, and prevents exactly this outcome when it isn't. Applies to any local-machine audit, not just this one; also applies before handing a file path to a separate CLI agent (zcode/agy/etc.) for review — pass an explicit exclusion list of paths/filenames rather than trusting the other agent to infer sensitivity on its own.
