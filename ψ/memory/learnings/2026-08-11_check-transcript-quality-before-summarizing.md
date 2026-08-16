---
pattern: When an ASR/transcript pipeline returns garbled or nonsensical text, verify readability before summarizing — don't interpret noise as content
date: 2026-08-11
source: "rrr: ayami-oracle"
concepts: [transcription, asr-quality, verification, whisper-fallback]
---

# Check transcript quality before summarizing

An automated transcription pipeline (a desktop app's built-in speech-to-text) can silently
produce garbage output — e.g. picking up background noise as speech and emitting fluent-looking
but meaningless multilingual text — with no error flag anywhere in its data model (status still
said "available", not "failed"). Trusting the presence of transcript rows is not the same as
trusting their content.

## What happened

Recovering a meeting summary for the user, a local SQLite-backed desktop app's own transcript
table had 18 rows for the target recording, all on one channel, reading as fluent-looking but
meaningless multilingual gibberish ("quería hacerlo en juif folio un po'se con andame..."). It
would have been easy to synthesize a plausible-sounding summary from fragments of this text.
Reading the actual content first (not just checking row count / non-null) revealed it wasn't
language at all — just ASR noise. Falling back to the raw audio (recovered from the app's stored
stream URL) and running local whisper-cpp on it produced a fully coherent, readable transcript
covering the same time window.

## The fix

Before summarizing any transcript (app-generated, ASR, OCR, or otherwise extracted text), read
enough of the actual content to judge whether it is coherent language, not just whether the
field is populated. If it reads as noise / nonsense / disconnected fragments, say so explicitly
rather than trying to extract meaning from it — and look for a raw-source fallback (original
audio/video/image) to re-process with a tool you control (e.g. local whisper-cpp) instead of
trusting the upstream pipeline's output at face value.

See also: [[2026-08-08_session-detection-breaks-under-concurrent-forks]] — same root habit
(sanity-check extracted data against what it should actually contain before trusting it) applied
in a different context (session timestamp mining) in the same session this lesson was written.
