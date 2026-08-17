"""Streamlit dashboard: live entry/exit signal view for the watchlist symbols in
backtester/cloud_run.py's SYMBOLS (single source of truth, shared with the Railway cron).

This is a live analysis view, independent of the actual running paper-trade state (which
lives on Railway's mounted volume, not here) — it recomputes each symbol's own strategy
signal fresh from current data every time (looked up per-symbol from cloud_run.py's
SYMBOLS via the STRATEGIES registry, not hardcoded to one strategy name — caught during
the 2026-08-15 book_rsi_ma → book_rsi_ma_mtf switch, before it shipped out of sync), same
math the cron job uses, but doesn't touch position state.

Run: streamlit run dashboard.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backtester import indicators as ind
from backtester.cloud_run import SYMBOLS
from backtester.data import fetch_ohlcv
from backtester.strategy import STRATEGIES
from backtester.trade_store import (
    get_all_entries,
    get_all_real_trade_notes,
    get_all_trades,
    get_last_heartbeat,
    is_connected,
)

st.set_page_config(page_title="Market Backtester — Live Signals", layout="wide")
st.title("📊 Market Backtester — Live Entry/Exit Signals")
st.caption(
    "กลยุทธ์ตามที่ตั้งไว้ต่อสัญลักษณ์ใน cloud_run.py (ปัจจุบันคือ book_rsi_ma_mtf ทุกตัว — "
    "RSI(5)+SMA(20) รายวัน กรองด้วยเทรนด์รายสัปดาห์) — วิเคราะห์สดจากข้อมูลจริง "
    "ไม่ใช่สถานะ paper-trade ที่รันจริงบน Railway (แยกกัน)"
)

# Cron runs every 6h max (4x/day); >8h since the last confirmed run means a check was
# missed — this is exactly the failure mode that motivated this check in the first place
# (Railway's cronSchedule can silently go dead with zero errors anywhere). See README's
# "Known bug (critical)" section.
_HEARTBEAT_STALE_HOURS = 8
_last_heartbeat = get_last_heartbeat()
if _last_heartbeat is None:
    st.warning(
        "⚠️ ยังไม่เคยได้รับสัญญาณจาก cron job เลย (heartbeat ว่างเปล่า) — "
        "อาจเป็นเพราะยังไม่เคยรันตั้งแต่ติดตั้งฟีเจอร์นี้ หรือ cron หยุดทำงาน เช็ค `railway logs --service market-backtester-advise` ได้เลย"
    )
else:
    age = datetime.now(timezone.utc) - datetime.fromtimestamp(_last_heartbeat, tz=timezone.utc)
    last_run_str = datetime.fromtimestamp(_last_heartbeat, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if age > timedelta(hours=_HEARTBEAT_STALE_HOURS):
        st.error(
            f"🚨 Cron job เงียบไปแล้ว {age.total_seconds()/3600:.1f} ชม. (รันครั้งล่าสุด: {last_run_str}) — "
            f"เกินกว่ากำหนด {_HEARTBEAT_STALE_HOURS} ชม. น่าจะหยุดทำงาน เช็ค Railway ด่วน "
            f"(ดู README 'Known bug' — cronSchedule อาจหลุดอีกรอบ)"
        )
    else:
        st.caption(f"✅ Cron job ล่าสุดรันเมื่อ {last_run_str} ({age.total_seconds()/3600:.1f} ชม. ที่แล้ว)")


@st.cache_data(ttl=300)
def load_symbol_data(symbol: str, market: str, strategy_name: str, params: dict) -> pd.DataFrame:
    df = fetch_ohlcv(symbol, market, "2024-08-01", None)
    df["RSI5"] = ind.rsi(df["Close"], 5)
    df["SMA20"] = ind.sma(df["Close"], 20)
    df["Signal"] = STRATEGIES[strategy_name](df, **params)
    return df


def pct_bullish(df: pd.DataFrame, months: int) -> float:
    cutoff = df.index[-1] - pd.DateOffset(months=months)
    window = df[df.index >= cutoff]
    if window.empty:
        return float("nan")
    return float(window["Signal"].mean() * 100)


rows = []
data_cache: dict[str, tuple[pd.DataFrame, dict]] = {}
for cfg in SYMBOLS:
    symbol, market = cfg["symbol"], cfg["market"]
    try:
        df = load_symbol_data(symbol, market, cfg["strategy_name"], cfg["params"])
        data_cache[symbol] = (df, cfg)
        latest = df.iloc[-1]
        is_bullish = latest["Signal"] == 1
        rows.append(
            {
                "Symbol": symbol,
                "Market": market,
                "Price": round(float(latest["Close"]), 5),
                "RSI(5)": round(float(latest["RSI5"]), 1),
                "SMA(20)": round(float(latest["SMA20"]), 5),
                "Signal": "🟢 BULLISH" if is_bullish else "⚪ flat",
                "Stop (if entered now)": round(float(latest["Close"]) * (1 - cfg["stop_pct"]), 5) if is_bullish else None,
                "Target (if entered now)": round(float(latest["Close"]) * (1 + cfg["target_pct"]), 5) if is_bullish else None,
                "% bullish, last 6mo": round(pct_bullish(df, 6), 1),
                "% bullish, last 12mo": round(pct_bullish(df, 12), 1),
            }
        )
    except Exception as e:
        rows.append({"Symbol": symbol, "Market": market, "Signal": f"error: {e}"})

st.subheader(f"ภาพรวม — {len(SYMBOLS)} ตัวใน watchlist")
st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
st.caption(
    "\"% bullish\" = สัดส่วนวันที่ผ่านมาที่ RSI(5)>50 และราคาอยู่เหนือ SMA(20) พร้อมกัน "
    "(คำนวณจริงจากข้อมูลย้อนหลัง ไม่ใช่ค่าประมาณ)"
)

st.subheader("ดูรายละเอียดรายตัว")
selected = st.selectbox("เลือกสัญลักษณ์", [c["symbol"] for c in SYMBOLS])

if selected in data_cache:
    df, cfg = data_cache[selected]
    tail = df.tail(180)

    price_fig = go.Figure()
    price_fig.add_trace(go.Scatter(x=tail.index, y=tail["Close"], name="Close", line=dict(color="#4C9AFF")))
    price_fig.add_trace(go.Scatter(x=tail.index, y=tail["SMA20"], name="SMA(20)", line=dict(color="orange", dash="dot")))
    bullish_days = tail[tail["Signal"] == 1]
    price_fig.add_trace(
        go.Scatter(
            x=bullish_days.index,
            y=bullish_days["Close"],
            mode="markers",
            name="Bullish days",
            marker=dict(color="green", size=5),
        )
    )
    price_fig.update_layout(title=f"{selected} — Price + SMA(20)", height=420, margin=dict(t=40))
    st.plotly_chart(price_fig, width="stretch")

    rsi_fig = go.Figure()
    rsi_fig.add_trace(go.Scatter(x=tail.index, y=tail["RSI5"], name="RSI(5)", line=dict(color="purple")))
    rsi_fig.add_hline(y=50, line_dash="dash", line_color="gray")
    rsi_fig.update_layout(title=f"{selected} — RSI(5)", height=250, margin=dict(t=40))
    st.plotly_chart(rsi_fig, width="stretch")

    latest = df.iloc[-1]
    if latest["Signal"] == 1:
        stop = float(latest["Close"]) * (1 - cfg["stop_pct"])
        target = float(latest["Close"]) * (1 + cfg["target_pct"])
        st.success(f"**BULLISH** — เข้าที่ ~{latest['Close']:.5f}, stop-loss {stop:.5f}, take-profit {target:.5f}")
    else:
        st.info("ยังไม่เข้าเงื่อนไข RSI+MA — รอสัญญาณ (WAIT)")

st.divider()
st.subheader("ประวัติการเทรด (Trade History)")
st.caption(
    "เทรดที่ปิดจริงจาก paper-trading loop บน Railway (บันทึกผ่าน Redis เพื่อให้ dashboard "
    "เห็นข้อมูลเดียวกับ cron job — คนละ service กัน ไม่ได้ใช้ volume ร่วมกัน)"
)

trades = get_all_trades()
if not trades:
    if is_connected():
        st.info(
            "เชื่อมต่อ Redis สำเร็จ — แค่ยังไม่มีเทรดไหนปิดจริง (ทุกตำแหน่งยัง HOLD/WAIT อยู่) "
            "ตารางนี้จะขึ้นข้อมูลเองทันทีที่มีการปิดสถานะจริงครั้งแรก ไม่ต้องตั้งค่าอะไรเพิ่ม"
        )
    else:
        st.warning("⚠️ เชื่อมต่อ Redis ไม่ได้ — เช็คว่าตั้งค่า REDIS_URL ใน service นี้ถูกต้องหรือยัง")
else:
    trades_df = pd.DataFrame(trades).sort_values("exit_date", ascending=False)
    trades_df["return_pct"] = trades_df["return_pct"] * 100  # stored as a fraction, display as %

    total_pnl = trades_df["pnl"].sum()
    win_rate = (trades_df["pnl"] > 0).mean() * 100
    col1, col2, col3 = st.columns(3)
    col1.metric("จำนวนเทรดที่ปิดแล้ว", len(trades_df))
    col2.metric("กำไร/ขาดทุนรวม", f"{total_pnl:+,.2f}")
    col3.metric("Win rate", f"{win_rate:.1f}%")

    # Field has been on every Redis-stored trade since record_trade() first shipped
    # (trade_store.py), but this fills a default rather than KeyError-ing if an older
    # trade record on disk somehow predates that field.
    trades_df["strategy"] = trades_df.get("strategy", "unknown")

    st.markdown("**สรุปผลงานแยกตาม Symbol × Strategy**")
    breakdown_df = (
        trades_df.groupby(["symbol", "strategy"], as_index=False)
        .agg(
            trades=("pnl", "count"),
            win_rate=("pnl", lambda s: (s > 0).mean() * 100),
            total_pnl=("pnl", "sum"),
            avg_return_pct=("return_pct", "mean"),
        )
        .sort_values("total_pnl", ascending=False)
    )
    st.dataframe(
        breakdown_df,
        width="stretch",
        hide_index=True,
        column_config={
            "symbol": st.column_config.TextColumn("Symbol"),
            "strategy": st.column_config.TextColumn("Strategy"),
            "trades": st.column_config.NumberColumn("จำนวนเทรด"),
            "win_rate": st.column_config.NumberColumn("Win rate %", format="%.1f"),
            "total_pnl": st.column_config.NumberColumn("กำไร/ขาดทุนรวม", format="%+.2f"),
            "avg_return_pct": st.column_config.NumberColumn("Return เฉลี่ย %", format="%+.2f"),
        },
    )

    st.markdown("**รายการเทรดทั้งหมด**")
    st.dataframe(
        trades_df[
            ["symbol", "strategy", "market", "entry_date", "exit_date", "entry_price", "exit_price", "pnl", "return_pct", "exit_reason"]
        ],
        width="stretch",
        hide_index=True,
        column_config={"return_pct": st.column_config.NumberColumn("return %", format="%.2f")},
    )

st.divider()
st.subheader("สัญญาณ Paper vs เทรดจริง (Execution Tracker)")
st.caption(
    "เปรียบเทียบด้วยตา ไม่ใช่จับคู่อัตโนมัติ — ทั้งสองตารางเรียงเวลาล่าสุดก่อน "
    "ฝั่งขวามาจาก `บันทึกเทรด`/`เทรดจริง` ใน Discord ที่ส่งเข้ามาทาง `/api/log-real-trade` webhook "
    "(เก็บข้อความดิบ ไม่พาร์สตัวเลข — เหตุผลเดียวกับ `moss-real-trades.md` เอง)"
)
col_paper, col_real = st.columns(2)

with col_paper:
    st.markdown("**Paper entries** (จากกลยุทธ์)")
    entries = get_all_entries()
    if not entries:
        st.info("ยังไม่มีสัญญาณเข้าเลยตั้งแต่เพิ่มฟีเจอร์นี้")
    else:
        entries_df = pd.DataFrame(entries).sort_values("entry_date", ascending=False)
        st.dataframe(
            entries_df[["symbol", "market", "entry_date", "entry_price"]],
            width="stretch",
            hide_index=True,
        )

with col_real:
    st.markdown("**Real trades** (จาก Discord)")
    real_notes = get_all_real_trade_notes()
    if not real_notes:
        st.info("ยังไม่มีเทรดจริงส่งเข้ามาทาง webhook เลย")
    else:
        real_df = pd.DataFrame(real_notes).sort_values("recorded_at", ascending=False)
        real_df["logged_at"] = pd.to_datetime(real_df["recorded_at"], unit="s").dt.strftime("%Y-%m-%d %H:%M UTC")
        st.dataframe(
            real_df[["logged_at", "symbol_hint", "text"]],
            width="stretch",
            hide_index=True,
        )
