---
pattern: "Before telling anyone (or publishing) that a setting is/isn't a gate, count ALL occurrences and classify them; take UI labels from the product itself, not from the article that described it"
date: 2026-09-19
source: rrr: ayami-oracle
concepts: ["verification", "security-claims", "reverse-engineering", "public-post", "evidence-levels"]
---

# "No gate" claims need an exhaustive count + real UI labels

**Situation**: reviewing a blog claim that ZCode's Settings toggles don't stop a silent workspace upload. I verified one flag (`repoSnapshotIndexingEnabled`) and then said "both toggles don't stop it" — the second flag (`optimizeAgentExperienceEnabled`) was only sampled (script capped at 3 hits). I also used the blog's names for the toggles; the real on-screen labels were "Index new folders" and "Improve experience". Both went into a draft for a public post before I noticed.

**Rules**
1. **Absence needs an exhaustive count.** Search every occurrence, classify each (schema / migration / UI / logic), report "N total = a schema + b UI + c logic". A capped or sampled search proves presence, never absence.
2. **Take UI labels from the product, not the article.** Pull them from i18n/UI resources before writing text that tells readers where to click.
3. **Keep three evidence levels apart**: code exists → ran on this machine → known cause. "Code present, not triggered here, cause unknown" must not be shortened to "safe" or explained with a comforting reason.
4. **A passing mitigation test isn't safety.** `touch` failing on a locked dir proves the lock works, not that it stops the real process; name the stronger layer (sign out) first.
5. **In minified bundles, search by a unique unminified string** (message id, URL path, error name), then widen context — short minified identifiers (`YTe`, `Ke`) collide with unrelated code.

**Related**: [[2026-09-17_verify-existing-mechanism-before-extending-it]], [[2026-09-16_verify-subagent-claims-before-relaying-as-conclusion]], [[2026-09-15_dramatic-diagnostic-numbers-arent-automatically-confirming]], auto-memory `feedback_verify_before_asserting`
