---
pattern: "When delegating security-relevant code changes to any agent — including yourself mid-edit — write and run concrete test cases against actual before/after behavior before trusting a 'fixed' claim"
date: 2026-08-08
source: "rrr: ayami-oracle"
concepts: ["verification", "delegation", "security", "set-e", "bash"]
---

# Verify delegated security fixes with tests, not confidence

Delegated a review + fix of `.claude/hooks/safety-check.sh` to `/zcode` (a separate GLM-backed coding agent). It reported "all 14 issues fixed" with a clear, well-organized explanation. Running actual test cases (`echo '{"tool_input":{"command":"rm -rf /tmp/foo"}}' | bash safety-check.sh`) revealed the primary `rm -rf` protection — the single most important rule in the file — no longer matched anything at all. A second regression (multi-line command normalization) was also non-functional despite being named as fixed.

Fixing it directly introduced a fresh, different bug: `RM_SEGMENT=$(echo "$NORMALIZED" | grep -oE '...' | head -1)` under `set -euo pipefail`, with no `|| true` guard. Under `set -e`, a failing pipeline inside a plain `VAR=$(...)` assignment kills the script — unlike a failing command inside a `command && VAR=1` list, which is exempt. This blocked almost every command that didn't contain "rm". Caught only via a 19-case test suite plus a simulated agent-worktree (`mktemp -d` + `CLAUDE_PROJECT_DIR`).

**Rule**: a confident, well-structured explanation of a fix — from another agent or from yourself — is not evidence it works. For anything touching security/safety-critical logic, write test cases covering both "should still work" and "should still be blocked" before considering it done, and actually run them. Also: `set -e` semantics around command substitutions vs. `&&` lists are non-obvious enough to warrant testing the specific failure path rather than reasoning about it abstractly.

Secondary finding: this system's `/usr/bin/grep -E` supports `\s` as whitespace but `/usr/bin/sed` does not (BSD sed vs. the grep binary in use) — the same regex metacharacter can silently behave differently across sibling POSIX tools on the same machine.
