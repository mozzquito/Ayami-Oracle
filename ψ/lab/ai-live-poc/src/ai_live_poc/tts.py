"""Text -> speech via edge-tts (free, streaming-capable, no GPU).

Not a cloned voice — edge-tts serves Microsoft's stock neural voices. Real
voice cloning (OpenVoice / XTTS, per the zcode+agy architecture consult) is
the v2 swap-in; this module's synthesize() signature stays the same either
way so the rest of the pipeline doesn't need to change."""
from __future__ import annotations

import os
from pathlib import Path

import edge_tts

VOICE = os.environ.get("AI_LIVE_POC_VOICE", "th-TH-PremwadeeNeural")

AUDIO_DIR = Path(__file__).resolve().parents[2] / "audio"
AUDIO_DIR.mkdir(exist_ok=True)


async def synthesize(text: str, *, turn: int) -> Path:
    """Render text to an mp3 in audio/ and return its path."""
    out_path = AUDIO_DIR / f"turn_{turn:04d}.mp3"
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(str(out_path))
    return out_path
