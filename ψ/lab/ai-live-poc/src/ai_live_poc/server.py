"""FastAPI server: runs the orchestrator loop in the background and streams
its events to a browser page (public/index.html) over SSE. The avatar reacts
to the TTS audio's own amplitude (Web Audio API, client-side) — no separate
lip-sync model needed, per the "why this shape" note in README.md.
"""
from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import orchestrator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DIR = PROJECT_ROOT / "public"
AUDIO_DIR = PROJECT_ROOT / "audio"

_subscribers: list[asyncio.Queue[dict]] = []


async def _broadcast_loop() -> None:
    async for event in orchestrator.run(interval_seconds=5.0):
        for queue in list(_subscribers):
            queue.put_nowait(event)


@asynccontextmanager
async def _lifespan(_: FastAPI):
    task = asyncio.create_task(_broadcast_loop())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(lifespan=_lifespan)
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(PUBLIC_DIR / "index.html")


@app.get("/events")
async def events() -> StreamingResponse:
    queue: asyncio.Queue[dict] = asyncio.Queue()
    _subscribers.append(queue)

    async def gen():
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        finally:
            _subscribers.remove(queue)

    return StreamingResponse(gen(), media_type="text/event-stream")
