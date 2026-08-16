---
pattern: Never copy a secret value into a persistence layer with broader scope/lifetime than the file it already lives in, even for convenience
date: 2026-08-09
source: "rrr: ayami-oracle"
concepts: [security, memory, secrets, persistence]
---

# Don't widen secret scope for convenience

While writing a project-memory summary of an SSH-based Kubernetes investigation into the cross-repo auto-memory system (`~/.claude/projects/.../memory/`), the natural move was to also save the SSH password pattern there — it would make future sessions faster (no need to re-open the local credentials file). That impulse was caught before writing: the auto-memory system is deliberately broader-scoped and longer-lived than the single local file the credential already lived in (a project-local, gitignore-pending file). Copying the secret there would have widened its blast radius for a convenience that didn't require it — a *reference* to the file's location gives 100% of the same future-session value without the exposure.

**Rule**: before writing any credential, token, or secret into a persistence layer (memory, notes, retrospectives, cross-session state), ask whether that layer's scope/lifetime is broader than the secret's current home. If yes, store a *pointer* (file path, description of where it lives) instead of the value. This applies even when the target file is technically private/local — broader scope and longer lifetime are the risk factors, not just "is this readable by others."
