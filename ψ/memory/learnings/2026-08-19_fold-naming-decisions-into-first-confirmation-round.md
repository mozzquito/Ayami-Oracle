---
pattern: When a user confirms they want repo/project-shape decisions surfaced explicitly, include naming/identity choices (repo name, exact path) in that same confirmation round instead of deciding them unilaterally afterward — even low-risk ones that match an existing convention.
date: 2026-08-19
source: rrr: ayami-oracle
concepts: [askuserquestion, scope-confirmation, auto-mode, new-project-setup]
---

# Fold naming decisions into the first confirmation round

During a session building a new standalone repo (`claude-multi-agent-kit`), I ran
`AskUserQuestion` to confirm repo location (standalone vs. subfolder) and content
scope (README-only vs. README + copyable templates). The user answered both. I then
picked the actual repo name and exact local path myself and started creating
directories without folding that into the same question round.

It worked out fine — the name was descriptive and the path matched an existing
`~/Code/github.com/<owner>/<repo>` convention I'd just verified via `gh auth status`
— but it was still a naming decision made unilaterally right after the user had just
signaled (by answering a structured question set) that they wanted repo-shape
decisions surfaced rather than assumed.

**Why**: Auto Mode's default is to avoid stopping for clarifying questions and make
the reasonable call — but the moment a user has *already* engaged with an
AskUserQuestion round for a given decision class (here: "what does this repo look
like"), that's a strong signal the whole decision class — not just the specific
sub-questions asked — is one they want a say in. Splitting "location + scope" from
"name" into two separate implicit-vs-explicit tracks is inconsistent with what the
user just demonstrated they wanted.

**How to apply**: When starting a new project/repo and the user's request implies
several shape decisions (location, name, scope, visibility), batch all of them into
one `AskUserQuestion` call up front rather than asking about some and quietly
deciding others — especially the ones with public/permanent surface area, like a
GitHub repo name that becomes part of a URL. If a decision genuinely is low-stakes
and reversible (e.g. an internal variable name), it's fine to just decide it — but a
repo name isn't in that category once the repo gets pushed publicly.
