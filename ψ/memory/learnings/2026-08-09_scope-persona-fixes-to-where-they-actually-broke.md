---
pattern: When a user corrects an in-conversation persona slip, check whether stored artifacts (prompts, configs) already have it right before assuming a repo-wide fix is needed — and reuse existing automation conventions instead of inventing parallel ones
date: 2026-08-09
source: rrr: ayami-oracle
concepts: [persona-consistency, code-reuse, agy, ocr, line-check]
---

# Scope persona fixes to where they actually broke; reuse established call patterns

## Context

Mid-task, Boss corrected Ayami for using "ผม" (male first-person) instead of a female pronoun ("ayami oracle เป็นผู้หญิงนะ จะมาพูด ผม ไม่ได้"). Before treating this as a repo-wide persona bug, checked the existing `ψ/lab/discord-bot/bot.mjs` PERSONA prompt — it already specified female pronouns correctly, written in an earlier session. The slip was isolated to the current conversation's live behavior, not a stored artifact.

Later in the same session, building `ψ/lab/line-check/check-line.sh` (screencapture → OCR → summarize → log), reused the Discord bot's exact `agy -p <prompt> --model <model> --mode plan` invocation shape rather than designing a new calling convention for the same underlying quick-brain call.

## Rule for next time

1. **When corrected on an in-session behavior, verify scope before fixing broadly.** Check whether the "wrong" behavior is actually baked into a stored prompt/config (which would mean other surfaces are affected too) or was just this conversation's live drift. Grep/read the relevant persona prompt file first — don't assume either "it's fine everywhere" or "it's broken everywhere" without checking.
2. **Persist the correction as a memory/feedback entry**, not just an in-conversation acknowledgment — an in-session fix without a saved memory will silently regress in the next session.
3. **When building a new feature that needs the same underlying capability another feature already uses (e.g. "call the quick-brain to summarize something"), read that feature's existing code and reuse its exact call shape** rather than inventing a parallel convention. One consistent pattern for "how Ayami talks to her quick-brain" is easier to maintain than several slightly different ones scattered across `ψ/lab/*`.
