---
name: whisper
description: Transcribe an audio or video file to text offline using local whisper-cpp (no internet, no API key). Use when the user says "ถอดเสียง", "ถอดข้อความ", "transcribe", "whisper", or asks to turn a recording/meeting/video file into text locally instead of using VideoDB/call.md or a cloud API.
---

# /whisper — Offline audio/video transcription

> Local speech-to-text via `whisper-cpp` (Homebrew), Metal-accelerated on Apple Silicon.
> Installed 2026-08-10. No internet or API key required once the model is downloaded.

## Setup (already done on this machine)

- Binary: `whisper-cli` (installed via `brew install whisper-cpp`, at `/opt/homebrew/opt/whisper-cpp/bin/whisper-cli`)
- Model: `~/.local/share/whisper-cpp/models/ggml-medium.bin` (~1.5GB, multilingual — accurate for Thai + English)

If `whisper-cli` or the model is missing (fresh machine), reinstall:
```bash
brew install whisper-cpp
mkdir -p ~/.local/share/whisper-cpp/models
curl -L -o ~/.local/share/whisper-cpp/models/ggml-medium.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin
```

## Usage

**whisper-cli only accepts WAV.** For any other format (mp4, mov, m4a, mp3), convert with `ffmpeg` first:

```bash
ffmpeg -i input.mp4 -ar 16000 -ac 1 -c:a pcm_s16le output.wav
```

Then transcribe:

```bash
whisper-cli -m ~/.local/share/whisper-cpp/models/ggml-medium.bin -f output.wav
```

- Auto-detects language by default. To force Thai (more accurate than auto-detect for mixed/noisy audio):
  ```bash
  whisper-cli -m ~/.local/share/whisper-cpp/models/ggml-medium.bin -f output.wav -l th
  ```
- Output formats — add flags to write files alongside the input instead of just printing to stdout:
  - `-otxt` → plain `.txt`
  - `-osrt` → `.srt` subtitles (with timestamps)
  - `-ovtt` → `.vtt` subtitles
  - Combine multiple, e.g. `-otxt -osrt`

## Full one-shot example

```bash
ffmpeg -y -i meeting.mp4 -ar 16000 -ac 1 -c:a pcm_s16le /tmp/meeting.wav
whisper-cli -m ~/.local/share/whisper-cpp/models/ggml-medium.bin -f /tmp/meeting.wav -otxt -osrt
```

## Notes

- Fully offline — verified working with GPU (Metal, Apple M1) and CPU fallback.
- Independent of call.md/VideoDB — works on any audio/video file on disk.
- Do NOT use `zcode --attach` or `agy` for transcription — both were tested on a real
  video file (call.md's `resources/permissions.mp4`) and neither reliably processes
  audio: zcode admits it can't, and agy claimed to "process the video" but its stated
  reasoning didn't match ground truth from `ffprobe` (likely a hallucinated capability
  claim, not real multimodal audio analysis). Use whisper-cli for any real transcription
  need.
- `medium` model chosen as the default balance of speed/accuracy/size for Thai+English.
  For faster (less accurate) results swap to `ggml-small.bin` or `ggml-base.bin`; for
  best accuracy (slower, ~3GB) use `ggml-large-v3.bin` — same download URL pattern,
  just swap the filename.
