"""Error-alerting: send_error_alert no-ops safely without credentials, engine surfaces
per-symbol fetch failures as warnings, main.py alerts on both warnings and hard failures."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

from paper_trading.notify import send_error_alert


def test_send_error_alert_noop_without_credentials(monkeypatch):
    monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
    monkeypatch.delenv("REPORT_CHANNEL_ID", raising=False)
    assert send_error_alert("test message") is False


def test_send_error_alert_posts_when_configured(monkeypatch):
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("REPORT_CHANNEL_ID", "123456")
    mock_resp = MagicMock(status_code=200)
    with patch("paper_trading.notify.requests.post", return_value=mock_resp) as mock_post:
        assert send_error_alert("boom") is True
        assert mock_post.called
        call_kwargs = mock_post.call_args.kwargs
        assert "boom" in call_kwargs["json"]["content"]
        assert call_kwargs["headers"]["Authorization"] == "Bot fake-token"


def test_send_error_alert_swallows_request_exception(monkeypatch):
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("REPORT_CHANNEL_ID", "123456")
    import requests

    with patch("paper_trading.notify.requests.post", side_effect=requests.RequestException("down")):
        assert send_error_alert("boom") is False  # must not raise


def test_engine_surfaces_partial_fetch_failure_as_warning(tmp_path, monkeypatch):
    from paper_trading.config import Config
    from paper_trading.engine import run_daily
    from paper_trading.storage import Storage

    cfg = Config(
        data_dir=tmp_path,
        slot_usd=10.0,
        max_open=5,
        rsi_period=14,
        rsi_oversold=30.0,
        trend_ma_period=50,
        rsrs_window=18,
        rsrs_threshold=0.0,
        binance_base_url="https://data-api.binance.vision",
        klines_limit=200,
        symbols=["BTCUSDT", "BROKENUSDT"],
    )
    storage = Storage(cfg.data_dir)

    import pandas as pd
    from datetime import datetime, timezone

    def fake_fetch(symbol, base_url, limit=200, session=None):
        if symbol == "BROKENUSDT":
            raise RuntimeError("simulated fetch failure")
        now = datetime(2026, 9, 16, 12, 0, 0, tzinfo=timezone.utc)
        rows = []
        for i in range(60, -1, -1):
            open_dt = pd.Timestamp(now.replace(hour=0, minute=0, second=0, microsecond=0))
            open_dt = open_dt - pd.Timedelta(days=i)
            close_dt = open_dt + pd.Timedelta(days=1) - pd.Timedelta(milliseconds=1)
            rows.append(
                {
                    "open_time": pd.Timestamp(open_dt),
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.0 + i * 0.01,
                    "volume": 1.0,
                    "close_time": pd.Timestamp(close_dt),
                }
            )
        return pd.DataFrame(rows)

    with patch("paper_trading.engine.fetch_daily_klines", side_effect=fake_fetch):
        result = run_daily(cfg, storage)

    assert result["ok"] is True
    assert "warnings" in result
    assert any("BROKENUSDT" in w for w in result["warnings"])


def test_main_alerts_on_unhandled_exception(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("REPORT_CHANNEL_ID", "123456")

    import main as main_module

    with patch("main.run_daily", side_effect=RuntimeError("boom")), patch(
        "main.send_error_alert"
    ) as mock_alert:
        rc = main_module.main()

    assert rc == 1
    assert mock_alert.called
    assert "boom" in mock_alert.call_args.args[0]
