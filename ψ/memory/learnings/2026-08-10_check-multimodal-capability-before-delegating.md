---
pattern: Before delegating audio/image/binary tasks to a sibling coding agent (agy/zcode), verify it actually supports that input type — otherwise it may improvise its own (slow, uncontrolled) workaround
date: 2026-08-10
source: "rrr: ayami-oracle"
concepts: [delegation, multimodal, agy, zcode, tool-selection, icloud, background-tasks]
---

# Check multimodal capability before delegating to a sibling coding agent

## What happened

Asked to transcribe a voice memo, followed the user's instruction to delegate to `agy` (a
sibling coding CLI, multi-model backend including Gemini which does support audio). Two
failures followed:

1. First run: agy needed a shell-command permission that headless (`-p`) mode can't prompt
   for → auto-denied, no output.
2. Second run (`--dangerously-skip-permissions`): agy decided on its own to download
   `whisper-large-v3-turbo` locally and run ASR itself, instead of using its Gemini backend's
   native audio understanding — timed out mid-download/transcribe.

Only after both failed did a check of local tools reveal `mlx_whisper` was already installed
and worked directly, no permission fights, no model-download detour.

Separately: PowerPoint/PDF summarization requests routed to the same agent worked fine once
attempted directly (unzip+grep for OOXML text, `pdftotext`, `uv run --with openpyxl` for
xlsx) — text extraction is a much safer bet for CLI delegation than binary media.

And: when 5 architecture diagrams were pasted inline and the user again asked "zcode/agy
summarize this," the better move was reading the images directly (native vision) rather than
routing through the sibling agent at all — faster, no round-trip risk, and still transparent
about why the instruction wasn't followed literally.

## Why

A coding agent's CLI is not guaranteed to expose the underlying model's multimodal
capabilities the way a direct API call would — the agent may instead try to "solve" an
audio/image file the way it solves any file it can't natively handle: by writing code or
shelling out to a tool, which can spiral into slow, resource-heavy, uncontrolled behavior
(downloading a multi-GB model here). Text-shaped tasks (docs, pdf, xlsx as extracted text)
don't have this failure mode.

## How to apply

- Before delegating a non-text (audio/image/video) task to a sibling CLI agent, either (a)
  test capability with a trivial case first, or (b) check whether local tools already handle
  it directly — `mlx_whisper`, `pdftotext`, `ffmpeg`, `uv run --with <lib>` for one-off
  Python deps.
- If the current agent already has the needed capability natively (e.g. vision for images
  already in the conversation), prefer using it directly over routing through a sibling agent
  — even when the user asked for the sibling by name — and say why.
- If delegation is genuinely needed and the target agent times out or improvises a workaround
  that's clearly off-track (e.g. downloading a model instead of using an API), don't retry
  with broader permissions as the first fix — check for a simpler local path first.
