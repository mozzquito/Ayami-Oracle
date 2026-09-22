---
pattern: "artifact-design dark-mode CSS must literally follow @media{ :root:not(){} } order — reversed nesting silently breaks dark mode; also, agy -p can exceed a 180s foreground timeout even on plain design-opinion prompts"
date: 2026-09-22
source: "rrr: ayami-oracle"
concepts: [artifact-design, css, dark-mode, agy, zcode, consult-workflow, jev-scope]
---

# CSS dark-mode nesting order + agy foreground timeout

## What happened

Building `AYAMI-MANUAL.html` (an Artifact), wrote the dark-mode token block as:

```css
:root:not([data-theme="light"]){
  @media (prefers-color-scheme: dark){ --sky:#...; }
}
```

instead of the artifact-design skill's documented order:

```css
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){ --sky:#...; }
}
```

This was written *right after* reading the correct pattern in the quickstart guidance — not a knowledge gap,
a transcription slip while writing ~900 lines of CSS/HTML/JS in one pass. Caught it only via a deliberate
self-review read-back before publish, not automatically.

Separately, `agy -p --mode plan` (a plain design-opinion prompt, not a coding task) exceeded the 180s
foreground Bash timeout and had to fall back to background + notification, while `zcode -p` on the same
prompt returned well within 180s.

## Rule

1. **When writing artifact CSS that follows a documented token pattern (dark-mode, safe-area insets, etc.),
   copy the exact skeleton from the guidance and fill in values — don't reconstruct the structure from memory,
   even seconds after reading it.** Long single-pass HTML/CSS writes are exactly where transcription slips like
   reversed nesting happen, and a reversed `@media`/selector order fails silently (no error, just a theme that
   never applies) rather than loudly.
2. **Don't assume `zcode` and `agy` return in the same timeframe for the same prompt.** `agy -p` can exceed a
   180s foreground timeout even on a non-coding, plain-text design question. When consulting both in parallel,
   expect one call to background and plan to tell the user you're still waiting rather than assuming both land
   in the same turn.
3. **When a user names a specific consult tool for a task outside that tool's documented scope** (e.g. asking
   `/jev` — a narrow external-text screening tool — for a general design opinion), skip the misuse and explain
   why in one line, rather than force-fitting a call for an answer that wouldn't mean anything. This matches
   Rule 6 (transparency) — a fabricated-scope tool call is its own kind of dishonesty.
