"""Environment-based configuration for paper trading."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DEFAULT_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "TRXUSDT",
    "BNBUSDT",
    "NEARUSDT",
    "POLUSDT",
    "SHIBUSDT",
]

STRATEGY_ORDER = ["book_rsi_ma_mtf", "rsrs_trend"]


@dataclass(frozen=True)
class Config:
    data_dir: Path
    slot_usd: float
    max_open: int
    rsi_period: int
    rsi_oversold: float
    trend_ma_period: int
    rsrs_window: int
    rsrs_threshold: float
    binance_base_url: str
    klines_limit: int
    symbols: list[str]


def _env_float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def load_config() -> Config:
    symbols_raw = os.getenv("SYMBOLS", "").strip()
    if symbols_raw:
        symbols = [s.strip().upper() for s in symbols_raw.split(",") if s.strip()]
    else:
        symbols = list(DEFAULT_SYMBOLS)

    data_dir = Path(os.getenv("DATA_DIR", "./data")).expanduser().resolve()

    return Config(
        data_dir=data_dir,
        slot_usd=_env_float("SLOT_USD", 10.0),
        max_open=_env_int("MAX_OPEN", 5),
        rsi_period=_env_int("RSI_PERIOD", 14),
        rsi_oversold=_env_float("RSI_OVERSOLD", 30.0),
        trend_ma_period=_env_int("TREND_MA_PERIOD", 50),
        rsrs_window=_env_int("RSRS_WINDOW", 18),
        rsrs_threshold=_env_float("RSRS_THRESHOLD", 0.0),
        binance_base_url=os.getenv("BINANCE_BASE_URL", "https://data-api.binance.vision").rstrip(
            "/"
        ),
        klines_limit=_env_int("KLINES_LIMIT", 200),
        symbols=symbols,
    )
