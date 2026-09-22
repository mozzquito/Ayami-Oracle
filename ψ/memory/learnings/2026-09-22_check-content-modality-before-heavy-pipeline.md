---
pattern: Before running a single-modality pipeline (audio-only transcription, vision-only OCR) on a video, cheaply check which modality actually carries the content first
date: 2026-09-22
source: rrr: ayami-oracle
concepts: [video-processing, whisper, ocr, verify-before-acting, ambiguous-instructions]
---

# Check content modality before running a heavy single-modality pipeline

A request phrased as "แกะภาษา" (decode/extract the language) from a video file was
assumed to mean spoken audio and routed straight into `/whisper` — convert to WAV,
run whisper-cli, get "[no audio]", check volume, normalize, retry. The video actually
had no speech at all; it was a silent screen recording of someone filling a form, and
the "language" to extract was on-screen German text, i.e. a reading task, not a
transcription task. The user had to interrupt the tool call mid-pipeline to redirect.

**Why**: Thai "ภาษา" (and English "language" too) is genuinely ambiguous between
spoken and written content, and a video file can carry either. Running the full
audio pipeline (ffmpeg convert → whisper-cli → volumedetect → loudnorm → retry) costs
several tool calls and real wall-clock time; a single extracted frame or an `ffprobe`
stream listing costs one cheap call and immediately reveals whether there's a face/
speech track worth transcribing or just static screen content worth reading directly.

**How to apply**: When a request about a video/audio file is ambiguous about which
modality carries the meaningful content, do the cheapest possible check first —
extract one frame (`ffmpeg -vf "select=eq(n\,0)"` or similar) and/or read the stream
list (`ffprobe`) — before committing to a full single-modality pipeline. This is the
same "verify before asserting/acting" discipline as [[feedback_verify_before_asserting]],
applied specifically to picking which tool to run, not just which claim to make.
Related: [[project_evisa_wayama]] (the eVisa/Wayama project this particular video
turned out to belong to).
