---
pattern: "Once a PII-exclusion precedent is set with the user in a session (e.g. excluding an ID card scan), apply that same standard automatically to other personal-data forms that surface later — don't wait for a classifier or the user to flag it again"
date: 2026-08-11
source: "rrr: ayami-oracle"
concepts: [pii, privacy, precedent, self-review, git, evisa]
---

# Generalize a PII precedent within the session, don't re-derive it per file

## What happened

Early in a session, มอส and I agreed to exclude a personal ID card scan from a document set
being pushed to a private GitHub repo. Later in the *same session*, while writing a deeper
summary of a different document set (Taximail support guides), I copied real third-party email
addresses and names straight out of incident-log screenshots into the summary file I was about
to commit and push — the exact same category of concern (third-party PII, private repo or not)
that had just been resolved minutes earlier for the ID card. An auto-mode classifier blocked the
`Write` call before it landed; only then did I anonymize.

## Why

I treated the ID-card decision as a one-off fact about *that specific file* rather than as a
standing rule about *personal data in this repo*. Each new file got evaluated fresh instead of
inheriting the policy already agreed. This is the same shape as pattern-matching onto a narrow
precedent instead of generalizing it — the opposite failure of over-generalizing, but just as
costly: the safety net that caught it was external (a classifier), not internal (self-review).

## How to apply

- When a user sets a boundary on sensitive/personal data anywhere in a session ("don't include
  X"), treat it as a session-wide policy for *that category of data*, not a one-time answer
  about one file. Apply it proactively to every subsequent file touching the same repo/output,
  without waiting to be asked again.
- Before writing content extracted from screenshots, logs, or scanned documents into anything
  that will be committed or shared — even to a private destination — scan for third-party PII
  (names, emails, phone numbers, IDs) as a standing step, the same way you'd check for API keys
  or credentials.
- Don't treat "the repo is private" as a reason to skip this check — the boundary the user set
  (ID card) was already private-repo-scoped, so the standard was never about repo visibility in
  the first place.
- If a classifier or hook blocks an action you took, don't just retry with a workaround — ask
  what category of risk it caught and check whether the same category applies elsewhere in the
  current task before continuing.
