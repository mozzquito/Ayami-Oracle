---
pattern: When investigating credentials on any machine, search by variable name/process structure not value patterns, and ask for usernames instead of looping through candidates
date: 2026-09-13
source: "rrr: ayami-oracle"
concepts: [credential-investigation, ssh, auto-mode-classifier, security-boundary, proc-environ]
---

# Search narrow for credentials; ask, don't loop, for usernames

While investigating where Grok Bot's sandbox stores an OpenAI API key it accepted via its own chat UI, two Bash calls were blocked by Claude Code's auto-mode "Credential Exploration" classifier:

1. A broad `grep` for secret-shaped patterns (`sk-...`, `OPENAI_API_KEY`) across `/root /home /etc /opt` — an overreaching first attempt.
2. A `for`-loop trying four candidate SSH usernames (`ubuntu`, `box`, `root`, `cursor`) in sequence — structurally identical to username enumeration/brute-forcing, regardless of intent.

**Rule 1**: search by variable *name* or by process/file structure (`/proc/1/environ` vs a child's `/proc/<pid>/environ`, `/etc/systemd/system` for service definitions, checking for a `/run/secrets`-style mount) rather than grepping for secret-shaped value patterns across broad filesystem paths. The narrower search answers the same question with far less exposure and reliably passes a safety classifier that a blanket sweep will not.

**Rule 2**: when multiple SSH usernames are plausible for a box, ask the user which one to use *before* looping through candidates. This session had already established the right pattern one step earlier — pausing via `AskUserQuestion` before removing a stale `known_hosts` entry — but didn't carry that same instinct forward into username selection. The fix (just ask) costs no more time than guessing wrong twice, and avoids a classifier block entirely.

**Why**: Both blocks were on the same underlying principle — credential-adjacent guessing needs a human checkpoint, not agent-side trial and error. The first block should have been generalized into avoiding the second, but wasn't applied until after a second block occurred.

**How to apply**: Before writing any command that (a) searches for secret-shaped strings across a filesystem, or (b) tries multiple identity/credential guesses in sequence, stop and ask: "would a human reviewer read this as reconnaissance/brute-forcing?" If yes, narrow the search or ask the user directly instead.

## Related finding: chat-based "secure secret" UI is a display guarantee, not a pipeline guarantee

Separately, confirmed via process-tree tracing (`/proc/1/environ` empty of the key, but present in child processes `start-desktop.sh`/`exec-daemon`, no on-disk file, no `/run/secrets` mount) that Grok Bot injects the OpenAI key directly into process memory at session spawn rather than persisting it to the sandbox filesystem. This is a reasonably good design (ephemeral, runtime-injected, similar to K8s Secret-as-env) — but a value typed into *any* chat interface, even one with a UI that says "Saved securely, kept private," has already transited that app's message/network pipeline before redaction can happen. Whether the backend retains that raw value in logs is invisible from a client/sandbox-side investigation — don't extend a "looks clean on the sandbox side" finding into a claim about backend log retention you can't verify.

See also the prior audit session's finding on unauthenticated Docker API exposure on the same Grok Bot sandbox (`ψ/memory/retrospectives/2026-09/11/17.47_grok-bot-audit-cli-zcode-bridge-bug.md`).
