import { config, WATCHED_SYMBOLS } from "./config.js";
import type { IndicatorReading } from "./types.js";

// Verified live 2026-08-27 against the real v2 API — this was the second
// endpoint tried this session; the first attempt used the older
// api.taapi.io/rsi?secret=... shape (from a stale doc redirect) and got a
// blanket 401 on every auth variant tried. The real current endpoint is
// v2.taapi.io/indicator/<name> with an Authorization: Bearer header and a
// "timeframe" param (not "interval") — confirmed via docs.taapi.io/index.html
// and a live RSI + MACD call, both returned real BTC/USDT values.
const TAAPI_BASE = "https://v2.taapi.io";

async function getIndicator<T>(name: string, symbol: string): Promise<T> {
  const url = new URL(`${TAAPI_BASE}/indicator/${name}`);
  url.searchParams.set("exchange", "binance");
  url.searchParams.set("symbol", symbol);
  url.searchParams.set("timeframe", "1h");
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${config.taapiSecret}` },
  });
  if (!res.ok) throw new Error(`TAAPI ${name} ${res.status}: ${await res.text()}`);
  return (await res.json()) as T;
}

function technicalState(rsi: number): IndicatorReading["technicalState"] {
  if (rsi <= 30) return "oversold";
  if (rsi >= 70) return "overbought";
  return "neutral";
}

export async function getIndicatorReading(symbol: string): Promise<IndicatorReading | null> {
  try {
    const [rsiRes, macdRes] = await Promise.all([
      getIndicator<{ value: number[] }>("rsi", symbol),
      getIndicator<{ valueMACDHist: number[] }>("macd", symbol),
    ]);
    const rsi = rsiRes.value[0];
    const macdHist = macdRes.valueMACDHist[0];
    return { symbol, rsi, macdHist, technicalState: technicalState(rsi) };
  } catch (err) {
    console.warn(`  ⚠ TAAPI lookup failed for ${symbol}: ${(err as Error).message}`);
    return null;
  }
}

export async function getAllWatchedIndicators(): Promise<Map<string, IndicatorReading>> {
  const map = new Map<string, IndicatorReading>();
  for (const symbol of WATCHED_SYMBOLS) {
    const reading = await getIndicatorReading(symbol);
    if (reading) map.set(symbol, reading);
  }
  return map;
}
