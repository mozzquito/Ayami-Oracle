---
pattern: Reconcile conflicting statements about a production mapping against setup history before committing it, and make unattended retry loops log the caught error so a plain 404 is not reported as an opaque "FAILED after N tries".
date: 2026-09-21
source: rrr: ayami-oracle (evisa/Wayama n8n report automation)
concepts: [verify-before-asserting, config-mapping, retry-loops, n8n, observability]
---

# Reconcile conflicting config statements; never swallow the retry error

Two separate failures in the evisa n8n upload pipeline (2026-09-18 to 2026-09-20) had the same shape: a small unverified step at the start, then a long, confusing symptom at the end.

## 1. A later convenient answer overrode earlier evidence

Two Google Drive folder IDs had to be mapped to two report jobs. มอส's first message labelled them correctly, and the original DAC setup on 2026-09-13 used the same mapping. Later, a multiple-choice answer said the opposite, and I wrote the later answer into both production scripts without checking it against the earlier evidence. Files landed in the wrong folders for two days, and the eventual complaint ("please separate the folders") looked like a new feature request.

**Rule**: when two statements about a production mapping conflict (which ID, host or path belongs to which job), do not take the newest one. Cross-check against an independent record such as the original setup, an existing file's contents, or an old commit, or ask a single tie-break question. Only then write it into config that runs unattended.

## 2. The retry loop hid the reason

The Oracle upload script wrapped its request in `try { … } catch { Start-Sleep 5 }` three times, then printed `FAILED after 3 tries`. The real cause was HTTP 404 (the workflow had been replaced and the old webhook path no longer existed). The message made it look like a network or server problem, and the diagnosis needed server-side logs.

**Rule**: any unattended script with a retry loop must log the caught error on every failed attempt (for PowerShell, `$_.Exception.Message`). One line per attempt is enough to distinguish "wrong URL (404)" from "server down (timeout)" from "auth (401/403)" for whoever reads the log first.

## 3. Side note: check the live endpoint, not only the flag

After `n8n unpublish:workflow` plus a restart, the database showed the workflow inactive, but a GET probe still returned the "registered for POST" hint because a stale `webhook_entity` row remained. A deactivation is only confirmed by probing the live endpoint and comparing with a known-dead path's response.

## How to apply

- Before editing config that maps IDs to jobs, list every place the mapping was ever stated (chat, setup notes, old scripts, git history) and confirm they agree; if not, ask.
- When writing any retry loop for a scheduled job, add the caught-error message to the output in the same edit.
- After deactivating or removing anything network-facing, probe it and compare with a path that is known to be dead.
