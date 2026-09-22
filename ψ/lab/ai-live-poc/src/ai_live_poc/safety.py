"""Chat-comment safety screen.

Wraps ψ/lab/jev-gate's pure screen() logic (chunking, normalization, verdict
bands) for both inbound viewer comments and outbound LLM replies.

Two modes:
  - offline (default): a local keyword heuristic score_fn. No network call,
    no API key, safe to run repeatedly against mock/demo traffic.
  - jev (--use-jev / AI_LIVE_POC_USE_JEV=1): delegates scoring to TypeSafe's
    Jev via jev-gate's real score_fn. Costs a real API call per chunk and
    requires TYPESAFE_API_KEY. Per ψ/lab/jev-gate/README.md, jev is an
    ADVISORY-ONLY signal — "no_instructions_detected" is not "safe" — so its
    verdict here only gates the demo pipeline, it is not a security boundary.

This module intentionally does not vendor jev-gate's logic; it imports it
directly from ../../jev-gate/gate.py so both stay in sync with the one
prototype the rest of the repo already trusts.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

JEV_GATE_DIR = Path(__file__).resolve().parents[3] / "jev-gate"
if str(JEV_GATE_DIR) not in sys.path:
    sys.path.insert(0, str(JEV_GATE_DIR))

import gate as _jev_gate  # noqa: E402  (path insert must happen first)

# Small, obviously-incomplete heuristic — good enough to demo the "flag ->
# drop" branch of the pipeline offline. Not a substitute for jev or any real
# moderation system.
_SUSPICIOUS_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"ignore (all |previous |prior )?instructions",
        r"disregard (all |previous |prior )?(instructions|rules)",
        r"you are now",
        r"system prompt",
        r"reveal (your|the) (prompt|instructions)",
        r"jailbreak",
    ]
]


def _offline_score_fn(chunk: str) -> float:
    return 0.9 if any(p.search(chunk) for p in _SUSPICIOUS_PATTERNS) else 0.05


def screen_text(text: str, *, use_jev: bool | None = None, threshold: float = _jev_gate.THRESHOLD) -> dict:
    """Return jev-gate's screen() result dict: verdict in
    {no_instructions_detected, review, flagged, unscored}."""
    if use_jev is None:
        use_jev = os.environ.get("AI_LIVE_POC_USE_JEV", "") == "1"
    score_fn = _jev_gate.make_score_fn(os.environ.get("JEV_MODEL", _jev_gate.MODEL_DEFAULT)) if use_jev else _offline_score_fn
    result = _jev_gate.screen(text, score_fn, threshold=threshold)
    result["mode"] = "jev" if use_jev else "offline-heuristic"
    return result


def is_safe(result: dict) -> bool:
    """Pipeline gating policy for this POC: only 'flagged' blocks. 'review' and
    'unscored' pass through with a warning — matches jev-gate's own guidance
    that verdicts are advisory, not a hard safety boundary."""
    return result["verdict"] != "flagged"
