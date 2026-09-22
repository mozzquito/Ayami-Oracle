"""Ties the pipeline together: mock chat -> inbound safety -> turn gate ->
LLM response -> outbound safety -> TTS. Yields one event dict per processed
turn (or per drop), so both the CLI runner and the web server can consume
the same stream.

This is the v1 scope from the architecture review (ψ/active/context/
2026-09-22_ai-live-streaming-tiktok-shopee.md + the zcode/agy consults):
audio-only avatar, no real-time neural lip-sync (that needs a CUDA GPU this
Mac doesn't have) — the avatar/browser side just reacts to this event stream.
"""
from __future__ import annotations

import asyncio
from typing import AsyncIterator

from . import mock_chat, responder, safety, tts
from .queue_manager import TurnGate


async def run(*, max_turns: int | None = None, interval_seconds: float = 3.0, use_jev: bool | None = None) -> AsyncIterator[dict]:
    gate = TurnGate()
    processed = 0
    async for comment in mock_chat.stream(interval_seconds=interval_seconds):
        if max_turns is not None and processed >= max_turns:
            return

        inbound = safety.screen_text(comment.text, use_jev=use_jev)
        if not safety.is_safe(inbound):
            yield {
                "type": "dropped_inbound",
                "turn": comment.turn,
                "viewer": comment.viewer,
                "text": comment.text,
                "verdict": inbound["verdict"],
            }
            continue

        if not gate.admit(comment.text):
            yield {"type": "throttled", "turn": comment.turn, "viewer": comment.viewer, "text": comment.text}
            continue

        reply_text = await responder.reply_to(comment.text)

        outbound = safety.screen_text(reply_text, use_jev=use_jev)
        if not safety.is_safe(outbound):
            yield {
                "type": "dropped_outbound",
                "turn": comment.turn,
                "viewer": comment.viewer,
                "text": comment.text,
                "reply": reply_text,
                "verdict": outbound["verdict"],
            }
            continue

        audio_path = await tts.synthesize(reply_text, turn=comment.turn)
        processed += 1
        yield {
            "type": "spoken",
            "turn": comment.turn,
            "viewer": comment.viewer,
            "text": comment.text,
            "reply": reply_text,
            "audio_file": audio_path.name,
        }


async def _cli(max_turns: int = 5) -> None:
    print(f"ai-live-poc: running {max_turns} turns (mock chat, offline safety heuristic, Ollama qwen2.5, edge-tts)")
    async for event in run(max_turns=max_turns, interval_seconds=1.0):
        print(event)


if __name__ == "__main__":
    import sys

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    asyncio.run(_cli(n))
