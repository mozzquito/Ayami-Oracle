---
pattern: "Verify a CLI coding agent's self-reported capability claims (e.g. 'I processed this video') against independent ground truth before repeating them; and skip subagent delegation for small bounded tasks (~3-5 known files) since spin-up/wait latency can exceed just doing it directly"
date: 2026-08-10
source: "rrr: ayami-oracle"
concepts: ["verification", "delegation", "zcode", "agy", "whisper-cpp", "subagent-overhead", "mcp-debugging"]
---

# Verify CLI agent capability claims; don't over-delegate small tasks

Two related patterns from a session installing/debugging video-db/call.md and setting up
offline transcription:

1. **A CLI coding agent claiming success at a task outside its documented capability
   should be independently verified, not repeated as fact.** Tested zcode (GLM) and agy
   (Gemini) against a real video file (`call.md`'s `resources/permissions.mp4`, confirmed
   via `ffprobe` to have a real AAC audio stream). zcode honestly said it couldn't process
   audio/video. agy confidently claimed "I have successfully processed the video file
   using my tools" and concluded there was no audio track — which contradicted the
   `ffprobe` ground truth. Neither should be trusted for real transcription; installed
   `whisper-cpp` (Homebrew, Metal-accelerated) instead and verified it against a known
   sample (JFK speech, exact transcript match) before recommending it. See [[whisper]] skill.

2. **For small, bounded exploration tasks (read ~3-5 known files and summarize), doing it
   directly beats spawning a subagent and waiting.** A Haiku subagent tasked with writing
   a CODE-SNIPPETS doc from 5 known source files ran 9+ minutes across three status
   checks before being killed and the work done directly in under 5 minutes. Subagent
   spin-up + unpredictable latency can exceed the task itself for small, well-scoped
   jobs — reserve delegation for tasks that are genuinely large, parallel, or
   context-heavy.
