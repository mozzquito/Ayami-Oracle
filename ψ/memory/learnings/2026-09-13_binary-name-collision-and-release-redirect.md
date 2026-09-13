---
pattern: check which binary actually wins a naming collision empirically; use the releases/latest redirect instead of the rate-limited GitHub API for a release tag
date: 2026-09-13
source: rrr: ayami-oracle
concepts: [path-collision, cli-tools, github-releases, rate-limiting, verification]
---

# Two small, reusable installation habits

## 1. When two tools claim the same command name, test the real winner — don't assume

Installed both `maw-js` (Bun-based, already `bun link`ed) and `maw-rs` (Rust, via its official
installer) on the same box. Both ship a binary literally named `maw`. The maw-rs installer's own
output said `/home/box/.local/bin` was "not on PATH," which would have been easy to take at face
value and assume maw-js (already working via `~/.bun/bin/maw`) still won.

It didn't. A `bash -lc "which maw"` (a real login shell, matching how SSH automation actually
invokes commands) showed `~/.local/bin/maw` (maw-rs) winning — `~/.local/bin` gets added by
`~/.profile` for login shells, while `~/.bun/bin` was only ever added in `~/.bashrc`, which
login shells (as opposed to interactive non-login shells) don't automatically source. The
installer's own warning was accurate for *interactive* shells but not for the login-shell context
that actually mattered here.

**How to apply**: when two installed tools might collide on a command name, don't reason about
which "should" win from installer messages or `.bashrc` inspection alone — run the actual
resolution (`bash -lc "which <cmd>"` or equivalent for the real invocation context) and report
the measured winner, then let the human pick the intended default.

## 2. `releases/latest` redirect beats the GitHub API when you only need the tag

Needed the latest release tag for `typst` to download a specific asset. `api.github.com/repos/.../releases/latest` returned a 403 (unauthenticated rate limit, already spent by other calls this session). Fetching `https://github.com/typst/typst/releases/latest` with `curl -sSIL` and reading the `location:` response header (`.../releases/tag/v0.15.1`) resolved the same information without touching the API's rate limit at all — it's a plain web redirect, a completely separate bucket.

**How to apply**: reach for the redirect-header method first whenever the only thing needed is
"what's the latest tag," reserving the JSON API for when actual release metadata (assets list,
body, dates) is required beyond the tag name.
