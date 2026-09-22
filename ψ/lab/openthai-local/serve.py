"""Hardened local server for OpenThai-SystemOne: TypeSafe-compatible POST /v1/systemone on loopback only.

Why not the upstream server (openthai_systemone.server): it loads the model lazily through lru_cache, so several concurrent
first requests (or SDK retries after a 10 s timeout) each load their own ~3 GB copy; on an 8 GB machine that got the process killed
(exit 137). It also allows CORS from any origin and has no size limits. This wrapper reuses the upstream model/types unchanged.

  * model loaded ONCE at startup (before the first request), one inference at a time (lock)
  * no CORS middleware at all; Host header must be loopback (DNS-rebinding guard); optional bearer token
  * request size limits (state chars, question chars, number of questions) -> 413 instead of unbounded memory use

Run (from this directory, with the venv that has openthai-systemone installed):
  OPENTHAI_SYSTEMONE_MODEL=/path/to/model HF_HUB_OFFLINE=1 uvicorn serve:app --host 127.0.0.1 --port 8765
Env: OPENTHAI_DEVICE (mps|cpu|cuda; default auto), OPENTHAI_DTYPE (fp32|bf16|fp16; default fp32), OPENTHAI_LOCAL_TOKEN (optional),
     OPENTHAI_MAX_STATE_CHARS (default 150000), OPENTHAI_MAX_QUESTION_CHARS (20000), OPENTHAI_MAX_QUESTIONS (64).
"""
from __future__ import annotations

import hmac
import json
import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from openthai_systemone.types import SystemOneRequest, SystemOneResponse

ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}
MAX_STATE_CHARS = int(os.environ.get("OPENTHAI_MAX_STATE_CHARS", "150000"))
MAX_QUESTION_CHARS = int(os.environ.get("OPENTHAI_MAX_QUESTION_CHARS", "20000"))
MAX_QUESTIONS = int(os.environ.get("OPENTHAI_MAX_QUESTIONS", "64"))

_client = None
_lock = threading.Lock()


def load_client():
    import torch
    from openthai_systemone.client import SystemOneClient

    dtype = {"fp32": torch.float32, "bf16": torch.bfloat16, "fp16": torch.float16}[os.environ.get("OPENTHAI_DTYPE", "fp32")]
    return SystemOneClient(os.environ["OPENTHAI_SYSTEMONE_MODEL"], device=os.environ.get("OPENTHAI_DEVICE") or None,
                           dtype=dtype, model_name="openthai-systemone")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _client
    if _client is None:
        _client = load_client()  # eager, exactly once, before any request is accepted
    yield


app = FastAPI(title="OpenThai-SystemOne (local, hardened)", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def guard(request: Request, call_next):
    if (request.url.hostname or "") not in ALLOWED_HOSTS:  # DNS-rebinding guard
        return JSONResponse({"detail": "host not allowed"}, status_code=403)
    token = os.environ.get("OPENTHAI_LOCAL_TOKEN")
    if token and request.url.path != "/healthz":
        given = request.headers.get("authorization", "").removeprefix("Bearer ").strip()
        if not hmac.compare_digest(given.encode(), token.encode()):
            return JSONResponse({"detail": "unauthorized"}, status_code=401)
    return await call_next(request)


def check_limits(req: SystemOneRequest) -> None:
    state_chars = len(req.state) if isinstance(req.state, str) else len(json.dumps(req.state, ensure_ascii=False))
    q_chars = sum(len(json.dumps(q.model_dump(), ensure_ascii=False)) for q in req.questions.values())
    if state_chars > MAX_STATE_CHARS or q_chars > MAX_QUESTION_CHARS or len(req.questions) > MAX_QUESTIONS:
        raise HTTPException(status_code=413, detail="request too large for this local server")


@app.get("/healthz")
def healthz():
    return {"ok": True, "model_loaded": _client is not None}


@app.post("/v1/systemone", response_model=SystemOneResponse)
def system_one(req: SystemOneRequest):
    check_limits(req)
    with _lock:  # one inference at a time: bounded memory, no interleaving
        resp = _client.system_one(req.state, req.questions)
    resp.model = req.model or resp.model
    return resp
