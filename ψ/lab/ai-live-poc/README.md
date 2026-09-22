# ai-live-poc

Local, offline POC of an "AI digital-human live streaming" pipeline (the kind
used for TikTok Live / Shopee Live selling). **Not connected to any real
platform account.** Built to answer "how would this actually work" after
research into real open-source options found none that integrate directly
with TikTok Live or Shopee Live.

Architecture diagram (design stage, reviewed by zcode x2 + agy in parallel):
https://app.excalidraw.com/s/3oGho4k5kPa/2zLv6WU1IfH

Research this is based on: `ψ/active/context/2026-09-22_ai-live-streaming-tiktok-shopee.md`

## Why this shape

`lipku/LiveTalking` (the most complete real open-source pipeline found —
9.6k★, avatar render + voice clone + RTMP in one repo) needs CUDA and
12GB+ VRAM. This machine is an 8GB M1 with no dedicated GPU. Three
independent architecture reviews (zcode ×2, agy) converged on the same
verdict: skip real-time neural lip-sync locally, build an **audio-only /
2D-sprite avatar** pipeline that actually runs here, and treat
LiveTalking-on-a-rented-GPU as a v3 upgrade path, not v1.

## Pipeline (v1, built and partially verified)

```
mock chat -> jev inbound screen -> turn gate -> Ollama LLM -> jev outbound screen -> edge-tts -> browser avatar (SSE)
```

- `mock_chat.py` — simulated viewer comments (no real platform connection)
- `safety.py` — wraps `ψ/lab/jev-gate/gate.py`'s pure `screen()` logic. Defaults to an
  offline keyword heuristic (no network, no cost); set `AI_LIVE_POC_USE_JEV=1`
  (+ `TYPESAFE_API_KEY`) to route through real Jev instead. Jev is advisory
  only — see jev-gate's own README — so this gates the demo, not a real
  safety boundary.
- `queue_manager.py` — cooldown + dedup so replies don't overlap/spam
- `responder.py` — calls local Ollama (`OLLAMA_MODEL`, default `qwen2.5:7b`)
  for a short spoken reply; falls back to a canned line if Ollama doesn't
  answer in time
- `tts.py` — `edge-tts` (Thai voice by default: `th-TH-PremwadeeNeural`).
  Not a cloned voice yet — real voice cloning (OpenVoice/XTTS) is the v2 swap-in,
  `synthesize()`'s signature is written so that swap doesn't touch the rest
  of the pipeline.
- `server.py` — FastAPI app. Runs `orchestrator.run()` as a background task
  and fans its events out over SSE (`GET /events`) to any connected browser
  tab; serves `public/index.html` at `/` and `audio/*.mp3` at `/audio/*`.
- `public/index.html` — single-page 2D sprite avatar (inline SVG face, no
  external assets/libs). Mouth openness is driven client-side by the TTS
  audio's own amplitude via the Web Audio API `AnalyserNode` (RMS of the
  time-domain buffer, sampled every animation frame) — this is the
  audio-only-avatar approach the architecture consult (zcode ×2 + agy)
  recommended instead of real-time neural lip-sync. A "▶ เริ่มไลฟ์" start
  button unlocks the `AudioContext` on first click, since browsers block
  autoplay-with-sound until a user gesture. Also renders a live chat feed
  (viewer comments, spoken replies, and throttled/blocked turns so the
  safety gate's effect is visible, not hidden).

## Verified so far (2026-09-22)

- `uv sync` installs clean.
- Pulled `qwen2.5:3b` (1.9GB) and set `OLLAMA_MODEL=qwen2.5:3b` — confirmed
  **real (non-fallback) LLM replies**, not just the canned line. First call
  after a cold Ollama load took ~60s (41s model load + 16s generation),
  which blew past `responder.py`'s old 15s timeout and silently fell back;
  bumped the timeout to 30s. Once the model is warm, a 3-turn run completed
  in ~43-64s total with zero fallback hits.
- `PYTHONPATH=src uv run python -m ai_live_poc.orchestrator 3` runs the full
  loop end-to-end: mock chat → offline safety screen → responder → edge-tts
  → real `.mp3` files written to `audio/`.
- `PYTHONPATH=src uv run uvicorn ai_live_poc.server:app --port 8731` — server
  starts, `GET /` returns 200, `GET /events` streams real SSE events
  (`spoken`, `throttled`, etc.), and the `.mp3` files it references are
  served correctly at `/audio/<file>.mp3` (200, not 404). Verified with curl
  only — **the browser page itself (avatar rendering, mouth animation,
  autoplay-unlock button) has not been opened in an actual browser yet.**
- Remaining known gap: `responder.py`'s 30s timeout still won't cover a full
  *cold* model load (41s observed) if Ollama evicts the model between calls
  (default TTL is short) — a long-idle live session would hit fallback again
  on the first reply after an idle gap. Not fixed; keeping the model warm
  (e.g. periodic no-op ping, or `ollama run <model> --keepalive -1`) is the
  likely fix, not attempted yet.

## Not yet built

- No OBS/RTMP output wiring (MediaMTX sink, per agy's suggestion) yet.
- Browser-side verification (see above) — only curl-tested so far.

## Run it

```bash
cd ψ/lab/ai-live-poc
uv sync
OLLAMA_MODEL=qwen2.5:3b PYTHONPATH=src uv run python -m ai_live_poc.orchestrator 5   # CLI: runs 5 turns, prints events
ls audio/                                                                            # generated .mp3 replies

# or, the browser avatar:
OLLAMA_MODEL=qwen2.5:3b PYTHONPATH=src uv run uvicorn ai_live_poc.server:app --port 8731
open http://localhost:8731/   # click "▶ เริ่มไลฟ์" to unlock audio, then watch it run
```

## Explicitly out of scope for this POC

No TikTok Live / Shopee Live account integration. Shopee requires
pre-approval for AI hosts and bans reused hosts across accounts; TikTok
requires labeling synthetic voice/face content (see the research doc for
citations, some flagged as needing re-verification). Going from this POC to
a real account is a separate decision with real ToS exposure — not something
to back into silently.
