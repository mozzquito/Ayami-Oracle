"""Turn-taking policy: dedup near-identical comments and enforce a minimum
cooldown between spoken replies, so the avatar doesn't try to answer faster
than it can render (the "spammy live stream" gap all three architecture
consults — zcode x2, agy — flagged independently)."""
from __future__ import annotations

import time
from collections import deque


class TurnGate:
    def __init__(self, *, cooldown_seconds: float = 2.0, dedup_window: int = 20):
        self._cooldown = cooldown_seconds
        self._recent = deque(maxlen=dedup_window)
        self._last_turn_at = 0.0

    def admit(self, text: str) -> bool:
        """True if this comment should be answered now."""
        now = time.monotonic()
        if now - self._last_turn_at < self._cooldown:
            return False
        if text in self._recent:
            return False
        self._recent.append(text)
        self._last_turn_at = now
        return True
