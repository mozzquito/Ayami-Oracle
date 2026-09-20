---
pattern: When creating an artifact bound for a public/external destination (public GitHub repo, public artifact, etc.), confirm naming/license/attribution with the user before publishing — visibility (public vs private) is not the only irreversible decision; content is too.
date: 2026-09-13
source: rrr: ayami-oracle
concepts: [public-publish, user-confirmation, git-repo-creation, sdlc-gate]
---

# Confirm naming/license before publishing, not just visibility

While building `claude-multi-agent-kit` (a standalone repo documenting how to wire Claude
Code up to sibling `/zcode`/`/agy` CLI agents), I asked the user to confirm repo location,
content scope, and public/private visibility via AskUserQuestion — but picked the repo
name (`claude-multi-agent-kit`), license (MIT), and copyright attribution (the user's real
name) unilaterally, then pushed to a public GitHub repo in the same step as confirming
"public" vs "private."

**The gap**: visibility and content are separate decisions. Asking "public or private?"
confirms *who can see it*, not *what they'll see*. A public repo is visible to anyone
immediately on push — there's no draft-review step once it's live. Naming and license
choices are cheap to get wrong privately but socially costly to redo publicly (renaming a
public repo breaks links, re-licensing after the fact raises questions).

**Rule**: before running `gh repo create --public` (or any equivalent "publish externally"
action) on generated content, either (a) show the user the concrete name/license/attribution
choices as part of the same confirmation question, or (b) default to private first and offer
to flip to public only after the user has seen the actual files. Don't bundle "should this
be public" with "here's what I already decided the content will say."

**How to apply**: this generalizes beyond git repos — any time an artifact, doc, or page
is about to become visible to people other than the requesting user (public GitHub repo,
shared artifact link, public gist, published page), treat naming/branding/attribution
choices as part of what needs sign-off, not just the visibility toggle.
