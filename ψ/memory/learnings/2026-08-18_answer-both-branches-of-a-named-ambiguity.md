---
pattern: When a user's own earlier answer explicitly names two possible interpretations, a later follow-up touching that same ambiguity should address both branches, not silently pick one
date: 2026-08-18
source: rrr: ayami-oracle
concepts: [ambiguity-handling, sql, user-communication]
---

# Answer both branches of a named ambiguity, don't silently pick one

During eVisa Oracle SQL follow-ups, มอส asked what "Visa Category" values exist for a group he'd
referred to as "NON-B." A session earlier, when directly asked to clarify what "NON-B" meant
(paired against "IMF CY"), มอส's own answer was "Visa Type/Category อีกกลุ่มหนึ่ง" — explicitly
naming *both* possible axes (Visa Type **or** Category) rather than picking one.

When the follow-up question came, I answered by querying `VISA_CATEGORY` only, without giving a
`VISA_TYPE_NAME` breakdown alongside it. That silently resolved an ambiguity มอส had deliberately
left open, on my own initiative, without saying so — if the real answer needed the Visa Type axis
instead, the query I gave wouldn't have surfaced it, and มอส would have to notice results didn't
look right before backtracking.

**Rule**: when a user's own prior answer explicitly names two (or more) possible interpretations
of something, and a later question touches that same ambiguity, give something that covers both
branches (e.g. two queries, or one combined breakdown) rather than silently committing to one.
Picking a "most likely" branch without naming the alternative reintroduces the exact ambiguity
that was already surfaced and deliberately left open — it just moves the discovery of the mismatch
later and makes it the user's job to catch.

**How to apply**: before answering a follow-up, check whether it touches a question the user
already answered ambiguously ("both", "not sure", "either"). If so, structure the answer as
"here's X for interpretation A, here's Y for interpretation B" rather than picking the
syntactically-first or most-obvious one and moving on.
