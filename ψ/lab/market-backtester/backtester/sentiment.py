"""Thai news sentiment overlay — ported from the ψ/lab/crypto-signal-digest Node.js
prototype (2026-08-27) into plain `requests` calls so the cron deployment stays
single-runtime (same rationale as notify.py: no Node dependency in the Railway image).

Scrapes real Thai financial headlines (Firecrawl), classifies sentiment per headline
(OpenRouter/DeepSeek), and checks whether that sentiment *aligns* with this system's own
already-computed technical signal (advisor.py's signal_now) for a watched crypto symbol —
deliberately NOT calling an external indicator API (TAAPI.io, used in the standalone
prototype) since market-backtester already computes real indicators from real price data
it fetches anyway; re-deriving the same information from a second paid API would be
redundant.

This module is designed to fail soft: every public function catches its own errors and
returns an empty/None result rather than raising, because a broken news scrape or a
flaky LLM call must never be allowed to interrupt the actual trading-signal pipeline
that calls it (see cloud_run.py's try/except wrapper around this module's entry point).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Literal, TypedDict
from urllib.parse import urlparse

import requests

from .advisor import STATE_DIR

FIRECRAWL_ENDPOINT = "https://api.firecrawl.dev/v1/scrape"
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat"

# Verified live 2026-08-27 in the crypto-signal-digest prototype — both return real,
# current Thai financial headlines via Firecrawl's markdown scrape. Two sources named in
# the original plan were dropped after live testing: moneychannel.co.th no longer
# resolves (the station shut down entirely — real news, not a broken link) and
# set.or.th's news page is a JS-rendered SPA that a basic scrape can't get past the
# shell of.
NEWS_SOURCES = [
    {"name": "Kaohoon", "url": "https://www.kaohoon.com/"},
    {"name": "ThairathMoney", "url": "https://www.thairath.co.th/money"},
]

# Maps this system's own SYMBOLS tickers (cloud_run.py) to keywords that identify a
# headline as being about that asset. Thai + English names/tickers both included since
# Thai financial press mixes both freely.
SYMBOL_KEYWORDS: dict[str, list[str]] = {
    "BTC": ["bitcoin", "บิทคอยน์", "บิตคอยน์", "btc"],
    "ETH": ["ethereum", "อีเธอเรียม", "eth"],
    "SOL": ["solana", "โซลาน่า", "sol"],
    "TRX": ["tron", "ทรอน", "trx"],
    "BNB": ["binance coin", "bnb"],
    "NEAR": ["near protocol", "near"],
}

Sentiment = Literal["positive", "negative", "neutral"]


class NewsItem(TypedDict):
    source: str
    title: str
    url: str


class SentimentResult(TypedDict):
    title: str
    url: str
    source: str
    subject: str
    sentiment: Sentiment
    reason: str


_MIN_TITLE_LENGTH = 12  # shorter than this is almost always a nav link, not a headline
_LINK_PATTERN = re.compile(r"\[\*{0,2}([^\]]+?)\*{0,2}\]\((https?://[^\s)]+)\)")


def _extract_headlines(markdown: str, source_name: str, source_url: str) -> list[NewsItem]:
    hostname = urlparse(source_url).hostname or ""
    seen: set[str] = set()
    items: list[NewsItem] = []
    for title, url in _LINK_PATTERN.findall(markdown):
        title = title.strip()
        if len(title) < _MIN_TITLE_LENGTH:
            continue
        if hostname not in url:
            continue
        if url in seen:
            continue
        seen.add(url)
        items.append({"source": source_name, "title": title, "url": url})
    return items


def fetch_headlines() -> list[NewsItem]:
    """Scrapes NEWS_SOURCES via Firecrawl. Returns [] (not an exception) on any failure —
    callers should treat an empty result as "no news this run", not as an error to
    surface urgently; the technical signal pipeline works fine without it.
    """
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        print("sentiment: FIRECRAWL_API_KEY not set, skipping news fetch", file=sys.stderr)
        return []

    all_items: list[NewsItem] = []
    for source in NEWS_SOURCES:
        try:
            resp = requests.post(
                FIRECRAWL_ENDPOINT,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"url": source["url"], "formats": ["markdown"], "onlyMainContent": True},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            markdown = data.get("data", {}).get("markdown", "")
            if not markdown:
                print(f"sentiment: Firecrawl returned no content for {source['name']}", file=sys.stderr)
                continue
            all_items.extend(_extract_headlines(markdown, source["name"], source["url"]))
        except requests.RequestException as e:
            print(f"sentiment: Firecrawl failed for {source['name']}: {e}", file=sys.stderr)
    return all_items


def _extract_json(raw: str) -> str:
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if fenced:
        return fenced.group(1).strip()
    start, end = raw.find("["), raw.rfind("]")
    if start != -1 and end != -1 and end > start:
        return raw[start : end + 1]
    return raw.strip()


def classify_sentiment(items: list[NewsItem]) -> list[SentimentResult]:
    """Batch-classifies headlines via OpenRouter/DeepSeek. Returns [] on any failure,
    same fail-soft contract as fetch_headlines().
    """
    if not items:
        return []
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("sentiment: OPENROUTER_API_KEY not set, skipping classification", file=sys.stderr)
        return []

    listing = "\n".join(f"{i}. {item['title']}" for i, item in enumerate(items))
    prompt = (
        "คุณคือนักวิเคราะห์ข่าวการเงิน วิเคราะห์หัวข้อข่าวต่อไปนี้ทีละข้อ\n"
        "สำหรับแต่ละข้อ ระบุ: บริษัท/เซกเตอร์/สินทรัพย์ที่พูดถึง (subject), "
        "sentiment (positive/negative/neutral), และเหตุผล 1 ประโยคสั้นๆ เป็นภาษาไทย (reason)\n\n"
        'ระวังสำนวนปฏิเสธซ้อน เช่น "ขาดทุนลดลง" คือ positive (ฟื้นตัว) ไม่ใช่ negative\n\n'
        f"หัวข้อข่าว:\n{listing}\n\n"
        "ตอบเป็น JSON array เท่านั้น ไม่มีคำนำ ไม่มี markdown code fence รูปแบบ:\n"
        '[{"index":0,"subject":"...","sentiment":"positive","reason":"..."}]'
    )

    try:
        resp = requests.post(
            OPENROUTER_ENDPOINT,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": MODEL, "messages": [{"role": "user", "content": prompt}]},
            timeout=30,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        parsed = json.loads(_extract_json(raw))
    except (requests.RequestException, KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"sentiment: OpenRouter classification failed: {e}", file=sys.stderr)
        return []

    results: list[SentimentResult] = []
    for entry in parsed:
        idx = entry.get("index")
        if idx is None or not (0 <= idx < len(items)):
            continue
        item = items[idx]
        results.append(
            {
                "title": item["title"],
                "url": item["url"],
                "source": item["source"],
                "subject": entry.get("subject", ""),
                "sentiment": entry.get("sentiment", "neutral"),
                "reason": entry.get("reason", ""),
            }
        )
    return results


def match_symbol(subject: str, title: str) -> str | None:
    """Returns the SYMBOLS ticker this classification is about, if any."""
    haystack = f"{subject} {title}".lower()
    for symbol, keywords in SYMBOL_KEYWORDS.items():
        if any(kw in haystack for kw in keywords):
            return symbol
    return None


AlignmentLabel = Literal["HIGH CONVICTION", "CONFLICTING"]


def check_alignment(symbol: str, signal_now: int, classified: list[SentimentResult]) -> list[tuple[SentimentResult, AlignmentLabel]]:
    """signal_now is this system's own real technical signal (1=bullish, 0=flat) from
    advisor.py — NOT a separate indicator API call. A positive-sentiment headline about a
    symbol that's currently signaling bullish reinforces the case (HIGH CONVICTION); a
    negative-sentiment headline on a bullish symbol is worth surfacing as a caution
    (CONFLICTING) rather than silently ignored, since this stays a decision-support tool,
    not an auto-trader.
    """
    matches: list[tuple[SentimentResult, AlignmentLabel]] = []
    for item in classified:
        if match_symbol(item["subject"], item["title"]) != symbol:
            continue
        if signal_now == 1 and item["sentiment"] == "positive":
            matches.append((item, "HIGH CONVICTION"))
        elif signal_now == 1 and item["sentiment"] == "negative":
            matches.append((item, "CONFLICTING"))
    return matches


# Persisted alongside advisor.py's own per-symbol state files (same STATE_DIR, so it
# lives on the same Railway volume and survives across cron runs) — tracks which
# headline URLs have already been classified so the same headline isn't reprocessed
# (burning an OpenRouter call) or re-notified every 2-hour cron tick.
_SEEN_PATH = STATE_DIR / "sentiment_seen_urls.json"
_MAX_SEEN = 2000  # cap so this can't grow unbounded over months of cron runs


def _load_seen() -> set[str]:
    if not _SEEN_PATH.exists():
        return set()
    try:
        return set(json.loads(_SEEN_PATH.read_text()))
    except (json.JSONDecodeError, OSError):
        return set()


def _save_seen(seen: set[str]) -> None:
    STATE_DIR.mkdir(exist_ok=True)
    trimmed = list(seen)[-_MAX_SEEN:]
    tmp_path = _SEEN_PATH.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(trimmed))
    tmp_path.replace(_SEEN_PATH)


def run_overlay(signal_now_by_symbol: dict[str, int]) -> list[str]:
    """One full overlay pass: fetch -> classify -> check alignment against each symbol's
    already-computed technical signal -> return formatted digest lines for anything new.

    Deliberately has no try/except of its own — cloud_run.py wraps the *call site* in a
    broad try/except instead, so a failure here is visible in cron logs with a full
    traceback rather than silently swallowed at multiple nesting levels.
    """
    seen = _load_seen()
    headlines = fetch_headlines()
    new_headlines = [h for h in headlines if h["url"] not in seen]
    if not new_headlines:
        return []

    classified = classify_sentiment(new_headlines)
    seen.update(h["url"] for h in new_headlines)
    _save_seen(seen)

    lines: list[str] = []
    for symbol, signal_now in signal_now_by_symbol.items():
        for item, label in check_alignment(symbol, signal_now, classified):
            emoji = "⚡" if label == "HIGH CONVICTION" else "⚠️"
            lines.append(
                f"{emoji} {symbol} [{label}] — {item['reason']}\n   ({item['source']}) {item['url']}"
            )
    return lines
