"""Environment-based configuration for the read-only Binance TH monitor."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

DEFAULT_BASE_URL = "https://api.binance.th"


@dataclass(frozen=True)
class Config:
    api_key: str
    api_secret: str
    base_url: str
    recv_window: int


def load_config() -> Config:
    api_key = os.getenv("BINANCE_TH_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_TH_API_SECRET", "").strip()
    if not api_key or not api_secret:
        raise RuntimeError(
            "BINANCE_TH_API_KEY / BINANCE_TH_API_SECRET must be set in .env "
            "(read-only key only — see README's Hard boundaries section)."
        )
    return Config(
        api_key=api_key,
        api_secret=api_secret,
        base_url=os.getenv("BINANCE_TH_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        recv_window=int(os.getenv("BINANCE_TH_RECV_WINDOW", "5000")),
    )
