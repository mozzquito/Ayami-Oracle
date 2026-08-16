---
pattern: "For a call.md/VideoDB meeting link, don't try WebFetch on the player URL (it's a SPA, returns nothing) — look up the recording in call.md's local SQLite DB by player_url, and if its live ASR transcript is garbled, fall back to downloading the raw audio from the recording's stream_url via ffmpeg and re-transcribing locally"
date: 2026-08-13
source: "rrr: ayami-oracle"
concepts: [videodb, call-md, transcription, sqlite, meeting-summary, whisper]
---

# Recovering a meeting summary from a call.md/VideoDB link

## What happened

User (มอส) shares a `https://player.videodb.io/watch?v=...` link and asks for a meeting
summary. Two separate sessions hit this same shape of task on the same day
(2026-08-13) and both found:

1. `WebFetch` on the VideoDB player URL returns nothing usable — it's a client-rendered
   SPA, not a page with fetchable content.
2. call.md (the local Electron meeting-recorder app มอส uses) stores its own metadata in
   a local SQLite DB at `~/Library/Application Support/call-md/data/call-md.db`. The
   `recordings` table has `player_url` and `stream_url` columns — query
   `SELECT * FROM recordings WHERE player_url = '<the shared link>'` to find the matching
   row instantly, including `meeting_name`, `meeting_description`, `meeting_checklist`
   (the pre-meeting agenda), and `insights_status`.
3. The app's own live transcript (`transcript_segments` table, joined on
   `recording_id`) is frequently **unusable** — its real-time ASR appears to be
   configured for or defaulting to English, so Thai speech comes out as nonsense English
   words (e.g. "tpc updates the data id", "lao do you need me and me keep up"). Don't
   summarize from this table without first eyeballing a sample for coherence.
4. When the live transcript is garbage, the `stream_url` column holds an HLS
   (`.m3u8`) stream that `ffmpeg` can pull directly: `ffmpeg -i "<stream_url>" -vn
   -acodec pcm_s16le -ar 16000 -ac 1 audio.wav`. Re-transcribe that locally with
   `mlx_whisper ... --language th --condition-on-previous-text False` (the
   hallucination-loop fix from the 2026-08-13 07:11 retro) for a clean Thai transcript.

## Why

call.md's own SQLite DB is the fastest, most reliable path to a VideoDB recording's
metadata and raw stream — faster than any web-based lookup, and it works offline. Its
live-transcription feature is a separate, less reliable subsystem (real-time ASR is
inherently harder than batch), so treat it as a nice-to-have shortcut, not a source of
truth, and always have the ffmpeg+local-whisper fallback ready.

## How to apply

- Given any `player.videodb.io` link, skip WebFetch entirely — go straight to the
  SQLite query on `call-md.db`.
- Before writing a summary from `transcript_segments`, read a handful of rows first. If
  they read as English word-salad for Thai audio, don't use them — pull `stream_url` and
  do the ffmpeg+local-whisper pipeline instead.
- `mlx_whisper` with `--condition-on-previous-text False` on Thai audio has now worked
  cleanly across two separate meetings in the same session (5 voice memos + this one) —
  treat it as the default flag, not an exception.
- `meeting_checklist` in the `recordings` table is the pre-meeting agenda (JSON array) —
  useful for structuring the summary and noting which planned items were actually
  covered vs. deferred.
