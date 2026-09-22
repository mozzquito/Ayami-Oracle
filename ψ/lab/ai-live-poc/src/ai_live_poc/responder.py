"""Turns a screened chat comment into a short spoken-reply script via a local
Ollama model. Falls back to a canned reply if Ollama isn't reachable, so the
rest of the pipeline (TTS, avatar) stays demoable without it."""
from __future__ import annotations

import os

import httpx

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")

SYSTEM_PROMPT = (
    "คุณคือพิธีกรไลฟ์ขายของ AI เป็นมิตร กระตือรือร้น พูดสั้น กระชับ ไม่เกิน 2 ประโยค "
    "ตอบคำถามของผู้ชมในแชทแบบเป็นธรรมชาติ ไม่ต้องทักทายซ้ำทุกครั้ง"
)

FALLBACK_REPLY = "ขอบคุณที่ทักมานะคะ เดี๋ยวแอดมินจะรีบตอบให้เร็วๆ นี้ค่ะ"


async def reply_to(comment_text: str, *, timeout: float = 30.0) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": comment_text},
        ],
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            text = data.get("message", {}).get("content", "").strip()
            return text or FALLBACK_REPLY
    except (httpx.HTTPError, KeyError, ValueError):
        return FALLBACK_REPLY
