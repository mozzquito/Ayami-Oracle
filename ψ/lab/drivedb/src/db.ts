/**
 * SQLite database layer with FTS5 full-text search.
 *
 * Schema: `files` table for metadata + `files_fts` virtual table for search.
 * Thai text is word-segmented via Intl.Segmenter before insertion so FTS5
 * (unicode61 tokenizer) can actually match Thai words.
 */

import Database from "better-sqlite3";
import { homedir } from "node:os";
import { join } from "node:path";
import { existsSync, mkdirSync } from "node:fs";

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

const DRIVEDB_DIR = join(homedir(), ".drivedb");
const DB_PATH = join(DRIVEDB_DIR, "drivedb.sqlite3");

/** Ensure ~/.drivedb exists and return the DB path. */
export function dbPath(): string {
  if (!existsSync(DRIVEDB_DIR)) {
    mkdirSync(DRIVEDB_DIR, { recursive: true });
  }
  return DB_PATH;
}

// ---------------------------------------------------------------------------
// Thai word segmentation
// ---------------------------------------------------------------------------

const thaiSegmenter = new Intl.Segmenter("th", { granularity: "word" });

/**
 * Segment Thai (and mixed-language) text into space-separated tokens.
 *
 * SQLite FTS5's default unicode61 tokenizer does NOT handle Thai word
 * boundaries because Thai has no whitespace between words.  By running
 * Intl.Segmenter first and re-joining with spaces, FTS5 can tokenize the
 * output normally.  English words pass through correctly too.
 */
export function segmentThai(text: string): string {
  const segments = thaiSegmenter.segment(text);
  const words: string[] = [];
  for (const seg of segments) {
    if (seg.isWordLike) {
      words.push(seg.segment);
    }
  }
  return words.join(" ");
}

// ---------------------------------------------------------------------------
// FTS5 query sanitization
// ---------------------------------------------------------------------------

/**
 * Wrap every individual search token in double quotes so FTS5 always treats
 * it as a literal phrase term, never as a boolean operator or special syntax.
 *
 * Without this, bare AND/OR/NOT keywords, unbalanced quotes, asterisks,
 * colons, or parentheses in user input crash the process with an uncaught
 * SqliteError (fts5 syntax error).
 */
function sanitizeFtsQuery(text: string): string {
  const tokens = text.split(/\s+/).filter((t) => t.length > 0);
  if (tokens.length === 0) return "\"\"";
  return tokens.map((t) => "\"" + t.replace(/"/g, "\"\"") + "\"").join(" ");
}

// ---------------------------------------------------------------------------
// Database init
// ---------------------------------------------------------------------------

export interface DB {
  db: Database.Database;
}

export function initDb(): DB {
  const path = dbPath();
  const db = new Database(path);

  // Enable WAL mode for better concurrent-read behaviour.
  db.pragma("journal_mode = WAL");

  // Main files table.
  db.exec(`
    CREATE TABLE IF NOT EXISTS files (
      id            INTEGER PRIMARY KEY AUTOINCREMENT,
      driveFileId   TEXT    NOT NULL,
      driveFileLink TEXT    NOT NULL,
      localPath     TEXT    NOT NULL,
      fileName      TEXT    NOT NULL,
      format        TEXT    NOT NULL,
      fileSize      INTEGER NOT NULL,
      duration      TEXT,
      transcript    TEXT    DEFAULT '',
      createdAt     TEXT    NOT NULL DEFAULT (datetime('now'))
    );
  `);

  // FTS5 virtual table — standalone (not content=files), because it stores
  // the Thai-word-segmented version of the text for tokenization, which is
  // deliberately DIFFERENT from the natural-language text kept in files.transcript
  // for display. Populated explicitly by insertFile/deleteFile in JS (not by
  // SQL triggers), since segmentation requires calling Intl.Segmenter.
  db.exec(`
    CREATE VIRTUAL TABLE IF NOT EXISTS files_fts
    USING fts5(transcript, fileName);
  `);

  // Timestamped transcript segments.
  db.exec(`
    CREATE TABLE IF NOT EXISTS segments (
      id      INTEGER PRIMARY KEY AUTOINCREMENT,
      fileId  INTEGER NOT NULL REFERENCES files(id),
      startMs INTEGER NOT NULL,
      endMs   INTEGER NOT NULL,
      text    TEXT NOT NULL
    );
  `);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_segments_fileId ON segments(fileId)`);

  // Migration: add `summary` column if it doesn't exist yet (idempotent).
  const columns = db.pragma("table_info(files)") as { name: string }[];
  if (!columns.some((c) => c.name === "summary")) {
    db.exec(`ALTER TABLE files ADD COLUMN summary TEXT`);
  }

  // Migration: add `tags` column if it doesn't exist yet (idempotent).
  if (!columns.some((c) => c.name === "tags")) {
    db.exec(`ALTER TABLE files ADD COLUMN tags TEXT`);
  }

  // Migration: add `summary` column to files_fts if missing (idempotent).
  // FTS5 virtual tables cannot be altered — must drop and recreate with
  // the new column, then backfill from the existing `files` table.
  const ftsRow = db.prepare(
    `SELECT sql FROM sqlite_master WHERE type='table' AND name='files_fts'`,
  ).get() as { sql: string } | undefined;
  if (!ftsRow?.sql.includes("summary")) {
    const migrateFts = db.transaction(() => {
      db.exec(`DROP TABLE IF EXISTS files_fts`);
      db.exec(`
        CREATE VIRTUAL TABLE files_fts
        USING fts5(transcript, fileName, summary);
      `);
      const rows = db
        .prepare(
          `SELECT id, transcript, fileName, summary FROM files`,
        )
        .all() as {
        id: number;
        transcript: string | null;
        fileName: string;
        summary: string | null;
      }[];
      const insert = db.prepare(
        `INSERT INTO files_fts (rowid, transcript, fileName, summary) VALUES (?, ?, ?, ?)`,
      );
      for (const row of rows) {
        insert.run(
          row.id,
          row.transcript ? segmentThai(row.transcript) : "",
          segmentThai(row.fileName),
          row.summary ? segmentThai(row.summary) : "",
        );
      }
    });
    migrateFts();
  }

  return { db };
}

// ---------------------------------------------------------------------------
// CRUD helpers
// ---------------------------------------------------------------------------

export interface FileRecord {
  id: number;
  driveFileId: string;
  driveFileLink: string;
  localPath: string;
  fileName: string;
  format: string;
  fileSize: number;
  duration: string | null;
  transcript: string;
  createdAt: string;
  summary: string | null;
  tags: string | null;
}

/**
 * Insert a new file record. `files.transcript` keeps the original,
 * natural-language text (for display via `show`/`list`). A separately
 * word-segmented copy is indexed into `files_fts` so Thai search works,
 * without polluting the display copy with artificial spacing.
 */
export function insertFile(
  db: Database.Database,
  record: Omit<FileRecord, "id" | "createdAt" | "summary" | "tags">,
): FileRecord {
  const stmt = db.prepare(`
    INSERT INTO files (driveFileId, driveFileLink, localPath, fileName, format, fileSize, duration, transcript)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `);

  const result = stmt.run(
    record.driveFileId,
    record.driveFileLink,
    record.localPath,
    record.fileName,
    record.format,
    record.fileSize,
    record.duration ?? null,
    record.transcript,
  );

  const id = Number(result.lastInsertRowid);

  const segmentedTranscript = record.transcript
    ? segmentThai(record.transcript)
    : "";
  db.prepare(
    `INSERT INTO files_fts (rowid, transcript, fileName, summary) VALUES (?, ?, ?, ?)`,
  ).run(id, segmentedTranscript, segmentThai(record.fileName), "");

  return getFileById(db, id)!;
}

/** Delete a file record and its FTS5 index entry. */
export function deleteFile(db: Database.Database, id: number): boolean {
  db.prepare(`DELETE FROM segments WHERE fileId = ?`).run(id);
  const result = db.prepare(`DELETE FROM files WHERE id = ?`).run(id);
  db.prepare(`DELETE FROM files_fts WHERE rowid = ?`).run(id);
  return result.changes > 0;
}

/** Get all files, newest first. */
export function listFiles(db: Database.Database): FileRecord[] {
  const stmt = db.prepare(`
    SELECT id, driveFileId, driveFileLink, localPath, fileName, format, fileSize, duration, transcript, createdAt, summary, tags
      FROM files
      ORDER BY id DESC
  `);
  return stmt.all() as FileRecord[];
}

/** Get a single file by ID. */
export function getFileById(
  db: Database.Database,
  id: number,
): FileRecord | undefined {
  const stmt = db.prepare(`
    SELECT id, driveFileId, driveFileLink, localPath, fileName, format, fileSize, duration, transcript, createdAt, summary, tags
      FROM files
      WHERE id = ?
  `);
  return stmt.get(id) as FileRecord | undefined;
}

/** Full-text search across transcripts and file names. */
export interface SearchResult {
  id: number;
  fileName: string;
  snippet: string;
}

export function searchFiles(
  db: Database.Database,
  query: string,
): SearchResult[] {
  // The indexed content is Thai-word-segmented (space-joined), so the query
  // must go through the same segmentation — otherwise a multi-word Thai
  // phrase typed without spaces becomes one giant unicode61 token that
  // can't match the separately-tokenized index (a single Thai word happens
  // to work by coincidence, but phrases would silently fail without this).
  const segmentedQuery = segmentThai(query) || query;
  const safeQuery = sanitizeFtsQuery(segmentedQuery);

  const stmt = db.prepare(`
    SELECT f.id, f.fileName,
           snippet(files_fts, -1, '«', '»', '…', 32) AS snippet
      FROM files_fts AS fts
      JOIN files AS f ON f.id = fts.rowid
      WHERE files_fts MATCH ?
      ORDER BY rank
      LIMIT 20
  `);
  return stmt.all(safeQuery) as SearchResult[];
}

// ---------------------------------------------------------------------------
// Segment helpers
// ---------------------------------------------------------------------------

export function insertSegments(
  db: Database.Database,
  fileId: number,
  segments: { startMs: number; endMs: number; text: string }[],
): void {
  if (segments.length === 0) return;
  const insert = db.prepare(
    `INSERT INTO segments (fileId, startMs, endMs, text) VALUES (?, ?, ?, ?)`,
  );
  const insertMany = db.transaction((segs: { startMs: number; endMs: number; text: string }[]) => {
    for (const s of segs) {
      insert.run(fileId, s.startMs, s.endMs, s.text);
    }
  });
  insertMany(segments);
}

export function getSegmentsByFileId(
  db: Database.Database,
  fileId: number,
): { id: number; fileId: number; startMs: number; endMs: number; text: string }[] {
  return db.prepare(
    `SELECT id, fileId, startMs, endMs, text FROM segments WHERE fileId = ? ORDER BY startMs ASC`,
  ).all(fileId) as { id: number; fileId: number; startMs: number; endMs: number; text: string }[];
}

/** Persist an AI-generated summary for a file record. */
export function updateSummary(
  db: Database.Database,
  id: number,
  summary: string,
): void {
  db.prepare(`UPDATE files SET summary = ? WHERE id = ?`).run(summary, id);
  // Keep FTS5 index in sync — segment the summary the same way as
  // transcript/fileName so Thai word boundaries are tokenized correctly.
  const segmentedSummary = summary ? segmentThai(summary) : "";
  db.prepare(`UPDATE files_fts SET summary = ? WHERE rowid = ?`).run(
    segmentedSummary,
    id,
  );
}

/** Persist tags for a file record. Caller is responsible for normalizing the string. */
export function updateTags(
  db: Database.Database,
  id: number,
  tags: string,
): void {
  db.prepare(`UPDATE files SET tags = ? WHERE id = ?`).run(tags, id);
}

/** Return all files whose tags contain the given tag as an exact comma-separated value. */
export function listFilesByTag(
  db: Database.Database,
  tag: string,
): FileRecord[] {
  const stmt = db.prepare(`
    SELECT id, driveFileId, driveFileLink, localPath, fileName, format, fileSize, duration, transcript, createdAt, summary, tags
      FROM files
      WHERE (',' || tags || ',') LIKE '%,' || ? || ',%'
      ORDER BY id DESC
  `);
  return stmt.all(tag.trim()) as FileRecord[];
}
