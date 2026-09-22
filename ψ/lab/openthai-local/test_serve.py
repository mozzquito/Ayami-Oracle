"""Offline tests for serve.py guards (fake model, no weights needed). Run with the venv that has openthai-systemone installed:
   /path/to/.venv/bin/python -m pytest -q"""
import threading
import time

import pytest
from fastapi.testclient import TestClient

import serve
from openthai_systemone.types import NoulAnswer, SystemOneResponse, Usage

BODY = {"state": "hello", "model": "m", "questions": {"q": {"type": "noul", "instructions": "is it hello?"}}}


class FakeClient:
    def __init__(self):
        self.calls = 0
        self.active = 0
        self.max_active = 0

    def system_one(self, state, questions):
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        time.sleep(0.02)
        self.calls += 1
        self.active -= 1
        return SystemOneResponse(model="fake", answers={"q": NoulAnswer(noul=0.9)}, usage=Usage(input_tokens=1))


@pytest.fixture()
def env(monkeypatch):
    fake = FakeClient()
    loads = []

    def fake_load():
        loads.append(1)
        return fake

    monkeypatch.setattr(serve, "load_client", fake_load)
    monkeypatch.setattr(serve, "_client", None)
    monkeypatch.delenv("OPENTHAI_LOCAL_TOKEN", raising=False)
    return fake, loads


def test_model_loaded_once_before_requests(env):
    fake, loads = env
    with TestClient(serve.app, base_url="http://127.0.0.1:8765") as c:
        assert c.get("/healthz").json() == {"ok": True, "model_loaded": True}
        for _ in range(3):
            assert c.post("/v1/systemone", json=BODY).status_code == 200
    assert len(loads) == 1


def test_concurrent_requests_are_serialised_and_share_one_model(env):
    fake, loads = env
    with TestClient(serve.app, base_url="http://127.0.0.1:8765") as c:
        results = []
        ts = [threading.Thread(target=lambda: results.append(c.post("/v1/systemone", json=BODY).status_code)) for _ in range(6)]
        [t.start() for t in ts]
        [t.join() for t in ts]
    assert results == [200] * 6 and fake.max_active == 1 and len(loads) == 1


def test_foreign_host_is_rejected(env):
    with TestClient(serve.app, base_url="http://evil.example") as c:
        assert c.post("/v1/systemone", json=BODY).status_code == 403


def test_no_cors_headers_for_foreign_origin(env):
    with TestClient(serve.app, base_url="http://127.0.0.1:8765") as c:
        r = c.post("/v1/systemone", json=BODY, headers={"Origin": "https://evil.example"})
        assert "access-control-allow-origin" not in {k.lower() for k in r.headers}


def test_size_limits(env, monkeypatch):
    monkeypatch.setattr(serve, "MAX_STATE_CHARS", 10)
    with TestClient(serve.app, base_url="http://127.0.0.1:8765") as c:
        assert c.post("/v1/systemone", json={**BODY, "state": "x" * 11}).status_code == 413
    monkeypatch.setattr(serve, "MAX_STATE_CHARS", 1000)
    monkeypatch.setattr(serve, "MAX_QUESTIONS", 0)
    with TestClient(serve.app, base_url="http://127.0.0.1:8765") as c:
        assert c.post("/v1/systemone", json=BODY).status_code == 413


def test_optional_token(env, monkeypatch):
    monkeypatch.setenv("OPENTHAI_LOCAL_TOKEN", "s3cret")
    with TestClient(serve.app, base_url="http://127.0.0.1:8765") as c:
        assert c.get("/healthz").status_code == 200
        assert c.post("/v1/systemone", json=BODY).status_code == 401
        assert c.post("/v1/systemone", json=BODY, headers={"Authorization": "Bearer wrong"}).status_code == 401
        assert c.post("/v1/systemone", json=BODY, headers={"Authorization": "Bearer s3cret"}).status_code == 200
