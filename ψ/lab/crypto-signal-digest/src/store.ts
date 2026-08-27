import Database from "better-sqlite3";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import type { Signal } from "./types.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, "..", "signals.sqlite");

const db = new Database(DB_PATH);
db.pragma("journal_mode = WAL");

db.exec(`
  CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    source TEXT NOT NULL,
    subject TEXT NOT NULL,
    sentiment TEXT NOT NULL,
    reason TEXT NOT NULL,
    indicator_symbol TEXT,
    rsi REAL,
    macd_hist REAL,
    conviction_label TEXT NOT NULL,
    sent_to_discord INTEGER NOT NULL DEFAULT 0
  );
`);

const insertStmt = db.prepare(`
  INSERT OR IGNORE INTO signals
    (title, url, source, subject, sentiment, reason, indicator_symbol, rsi, macd_hist, conviction_label)
  VALUES (@title, @url, @source, @subject, @sentiment, @reason, @indicator_symbol, @rsi, @macd_hist, @conviction_label)
`);

// Returns true if this was a genuinely new signal (false if it already
// existed — url has a UNIQUE constraint so re-running the pipeline on the
// same headlines doesn't duplicate rows or re-notify Discord).
export function saveSignal(signal: Signal): boolean {
  const result = insertStmt.run({
    title: signal.title,
    url: signal.url,
    source: signal.source,
    subject: signal.subject,
    sentiment: signal.sentiment,
    reason: signal.reason,
    indicator_symbol: signal.indicator?.symbol ?? null,
    rsi: signal.indicator?.rsi ?? null,
    macd_hist: signal.indicator?.macdHist ?? null,
    conviction_label: signal.convictionLabel,
  });
  return result.changes > 0;
}

export interface StoredSignal extends Signal {
  id: number;
  createdAt: string;
}

export function getUnsentSignals(limit = 10): StoredSignal[] {
  const rows = db
    .prepare(
      `SELECT * FROM signals WHERE sent_to_discord = 0 ORDER BY created_at DESC LIMIT ?`
    )
    .all(limit) as any[];
  return rows.map((r) => ({
    id: r.id,
    createdAt: r.created_at,
    title: r.title,
    url: r.url,
    source: r.source,
    subject: r.subject,
    sentiment: r.sentiment,
    reason: r.reason,
    indicator: r.indicator_symbol
      ? { symbol: r.indicator_symbol, rsi: r.rsi, macdHist: r.macd_hist, technicalState: "neutral" }
      : null,
    convictionLabel: r.conviction_label,
  }));
}

export function markSent(ids: number[]): void {
  if (ids.length === 0) return;
  const placeholders = ids.map(() => "?").join(",");
  db.prepare(`UPDATE signals SET sent_to_discord = 1 WHERE id IN (${placeholders})`).run(...ids);
}
