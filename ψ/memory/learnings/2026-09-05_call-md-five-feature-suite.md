---
pattern: "Shipped 5 features on call.md (Thai live+final translation, import/batch-process, zcode+agy second-opinion, FTS5 search) via a design->diff-review->live-test cycle with zcode+agy at every stage; verify-before-trust discipline for both second-opinion agents and Thai/non-Latin-script tokenization caught real bugs before shipping"
date: 2026-09-05
source: "rrr: call.md (video-db/call.md fork, mozzquito/call.md)"
concepts: ["learn", "call.md", "electron", "sqlite-fts5", "trigram-tokenizer", "thai-language-support", "zcode", "agy", "delegate-and-verify", "electron-abi-native-modules"]
---

# call.md five-feature suite: design->review->live-test discipline pays off

Across one long session (spanning 2026-09-04 to 2026-09-05), built and shipped 5 features
on a personal call.md fork: live EN→Thai translation, import & batch-process, second-opinion
AI summary (zcode+agy), Thai translation of the final summary, and FTS5 full-text search.
Every feature went through the same cycle: explore real codebase → design → implement →
self-review → zcode+agy diff review → verify their findings against source → fix → dev-test
→ live-test with real content → commit → push.

## Key technical facts worth remembering

1. **Trigram tokenizer, not word-tokenizer, for any search/index over Thai (or other
   non-space-delimited-script) text.** SQLite FTS5's default `unicode61` tokenizer splits on
   whitespace; Thai has none, so an entire paragraph becomes one unsearchable token.
   `tokenize='trigram'` indexes every 3-character window instead, giving substring search
   that works identically for English, Thai, or mixed text with zero word-segmentation.
   Verified this directly before designing around it, not after.

2. **Trigram's 3-character minimum interacts badly with naive AND-of-quoted-words query
   building.** A word under 3 characters can never match anything via trigram; ANDing an
   unmatchable phrase into a multi-word query zeros out the ENTIRE result set even when the
   other words genuinely match (`"launching" AND "AI"` → 0 rows, even though `"launching"`
   alone matches text containing "an AI project"). Fix: drop words under 3 chars from the
   query entirely rather than including them.

3. **better-sqlite3's native binary in an Electron app is ABI-compiled for Electron's Node,
   not the system/nvm Node.** Any ad-hoc script touching it via plain `node` segfaults
   silently (exit 139, no error text). Run it via
   `ELECTRON_RUN_AS_NODE=1 <path-to-electron-binary> script.js` instead - this is also the
   correct pattern for running a Node.js CLI tool (zcode) from inside an Electron app's main
   process, since a GUI-launched app doesn't inherit the user's shell PATH/nvm setup either.

4. **When translating/transforming structured data (JSON) via an LLM, always validate the
   parsed shape AND length against what was sent in - never trust `Array.isArray()` alone.**
   An LLM occasionally deviating from a requested JSON structure, if unvalidated, reaches
   whatever code consumes it downstream (a renderer's `.map()` calls) and can crash the UI.
   Also: on any translation/transform failure, return `null`/absent rather than falling back
   to the original-language text disguised as the translated result - silent language-mixing
   is worse than an absent section.

## Process lesson: delegate-and-verify held up, agy's reliability was inconsistent

zcode and agy caught real, concrete bugs at every diff-review round this session (the FTS5
short-word bug above, a summary-generation failure that would have discarded an
already-successful transcript, missing JSON shape validation, cross-recording state bleed in
a React component). The two-reviewer-plus-verify pattern from
[[feedback_delegate_verify_workflow]] is confirmed working well for this kind of
implementation work.

However, agy specifically made three separate confidently-wrong claims across this one
session: incorrect VideoDB SDK field names (`{path}` vs the actual `{filePath}`) it never
checked against the installed package's `.d.ts`, an incorrect Zod `.nullable()` claim
contradicted by the schema's own definition, and recommending an "action item checklist"
feature that already existed in the app. All three were caught by checking source before
applying - but the pattern (correct on architecture/security critique, unreliable on
specific verifiable facts about code it hasn't read) is worth remembering: treat any
second-opinion agent's *specific factual claim* about code/API shape as "check before
trust," even when its broader critique is sound and even within the same review.
