"""Error-alerting: send_error_alert no-ops safely without credentials, engine surfaces
per-symbol fetch failures as warnings, main.py alerts on both warnings and hard failures.
Trade-alerting: send_trade_alert formats entries/exits correctly, main.py only alerts on
real fills (not blocked_by_cap/already_open/invalid_price no-ops)."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

from paper_trading.notify import send_error_alert, send_trade_alert


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


def test_send_trade_alert_formats_entry(monkeypatch):
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("REPORT_CHANNEL_ID", "123456")
    trade = {
        "symbol": "BTCUSDT",
        "strategy": "book_rsi_ma_mtf",
        "side": "buy",
        "reason": "rsi_cross_up_trend",
        "price": 50000.1234,
        "qty": 0.0002,
        "pnl_usd": 0.0,
        "bar_date": "2026-09-16",
    }
    mock_resp = MagicMock(status_code=200)
    with patch("paper_trading.notify.requests.post", return_value=mock_resp) as mock_post:
        assert send_trade_alert(trade) is True
        content = mock_post.call_args.kwargs["json"]["content"]
        assert "ENTER" in content
        assert "BTCUSDT" in content
        assert "BTC_USDT" in content  # Binance link uses base_USDT, not the raw pair
        assert "rsi_cross_up_trend" in content


def test_send_trade_alert_formats_exit(monkeypatch):
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("REPORT_CHANNEL_ID", "123456")
    trade = {
        "symbol": "SHIBUSDT",
        "strategy": "rsrs_trend",
        "side": "sell",
        "reason": "take_profit",
        "price": 0.0000123,
        "qty": 500000.0,
        "pnl_usd": 0.51,
        "bar_date": "2026-09-16",
    }
    mock_resp = MagicMock(status_code=200)
    with patch("paper_trading.notify.requests.post", return_value=mock_resp) as mock_post:
        assert send_trade_alert(trade) is True
        content = mock_post.call_args.kwargs["json"]["content"]
        assert "EXIT" in content
        assert "SHIBUSDT" in content
        assert "SHIB_USDT" in content
        assert "+0.51" in content or "0.5100" in content


def test_main_skips_alert_for_blocked_and_noop_trades(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("REPORT_CHANNEL_ID", "123456")

    import main as main_module

    fake_result = {
        "ok": True,
        "skipped": False,
        "bar_date": "2026-09-16",
        "open_count": 1,
        "trades": [
            {"symbol": "BTCUSDT", "strategy": "book_rsi_ma_mtf", "side": "buy",
             "reason": "blocked_by_cap", "price": 100.0, "qty": 0.0, "pnl_usd": 0.0,
             "bar_date": "2026-09-16", "note": "ignored"},
            {"symbol": "ETHUSDT", "strategy": "book_rsi_ma_mtf", "side": "buy",
             "reason": "already_open", "price": 100.0, "qty": 0.0, "pnl_usd": 0.0,
             "bar_date": "2026-09-16", "note": "ignored"},
            {"symbol": "SOLUSDT", "strategy": "book_rsi_ma_mtf", "side": "buy",
             "reason": "rsi_cross_up_trend", "price": 100.0, "qty": 0.1, "pnl_usd": 0.0,
             "bar_date": "2026-09-16", "note": "opened"},
        ],
    }
    with patch("main.run_daily", return_value=fake_result), patch(
        "main.send_trade_alert"
    ) as mock_alert:
        rc = main_module.main()

    assert rc == 0
    assert mock_alert.call_count == 1  # only the real SOLUSDT fill, not the two no-ops
    assert mock_alert.call_args.args[0]["symbol"] == "SOLUSDT"
