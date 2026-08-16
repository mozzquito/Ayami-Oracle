---
pattern: "When asked to assess multiple similar-looking targets in a row (e.g. 'is this folder safe to delete'), check each one fresh — don't let the previous verdict set the depth of scrutiny for the next"
date: 2026-08-08
source: "rrr: ayami-oracle"
concepts: ["safety", "file-deletion", "judgment", "verification"]
---

# Don't anchor scrutiny on the previous verdict

Asked in sequence whether three folders were safe to delete. `arra-oracle-v3` and `namo-oracle` had near-identical *directory listings* at a glance — both showed names like `worktrees`, `projects`, `src`, `docs`, suggesting a real project layout. Only checking actual file counts and git remotes revealed the real difference: `arra-oracle-v3` was completely empty (3 `.DS_Store` files, no git repo), while `namo-oracle` was a real 156MB active project with a live GitHub remote and a personal file modified that same day.

Confirming the first folder was empty and safe could easily have made the second check feel redundant or lowered the bar for it — same-shaped question, similar-looking answer expected. It wasn't; the two folders needed completely different verdicts.

**Rule**: structural similarity between two "is X safe to delete" requests is not evidence of the same answer. Re-run the actual check (file count, git status/remote, recent-modification time) for each target rather than pattern-matching against the prior one in the same conversation — the risk is exactly in the case where surface appearance and actual content diverge.

Related: prefer a reversible action (move to Trash) over permanent deletion (`rm -rf`) for human-directed cleanup outside a git repo, even when the human uses the word "delete" — the word doesn't change the actual cost of being wrong.
