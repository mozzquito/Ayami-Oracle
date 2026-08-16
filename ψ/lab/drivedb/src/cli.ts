#!/usr/bin/env node

/**
 * drivedb — Personal video/audio transcriber CLI.
 *
 * Upload files to Google Drive, transcribe locally with whisper-cpp,
 * and search transcripts via SQLite FTS5.
 */

import { Command } from "commander";
import { resolve, basename, extname } from "node:path";
import { stat } from "node:fs/promises";
import { existsSync } from "node:fs";
import { initDb, insertFile, listFiles, getFileById, searchFiles, deleteFile, insertSegments, getSegmentsByFileId, updateSummary, updateTags, listFilesByTag } from "./db.js";
import { authenticate, getDriveClient, uploadFile } from "./drive.js";
import { createInterface } from "node:readline";
import { execFile } from "node:child_process";
import { transcribe, guessMimeType } from "./transcribe.js";
import { detectDevices, recordToFile, printDeviceSummary, cleanupTempFile } from "./record.js";
import { summarize } from "./summarize.js";
import { startServer } from "./server.js";

const VERSION = "1.0.0";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatBytes(bytes: number): string {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + " GB";
}

function formatMs(ms: number): string {
  const totalSecs = Math.floor(ms / 1000);
  const hrs = Math.floor(totalSecs / 3600);
  const mins = Math.floor((totalSecs % 3600) / 60);
  const secs = totalSecs % 60;
  if (hrs > 0) {
    return `${hrs}:${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  }
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

function padRight(str: string, len: number): string {
  return str.length < len ? str + " ".repeat(len - str.length) : str.slice(0, len);
}

// ---------------------------------------------------------------------------
// Shared pipeline (used by both upload and record)
// ---------------------------------------------------------------------------

/**
 * Transcribe a local file, upload to Drive, and store metadata in SQLite.
 *
 * This is the shared pipeline used by `cmdUpload` and `cmdRecord`.
 */
async function processAndStoreFile(
  absPath: string,
  displayName: string,
  /**
   * Path to record in the DB's `localPath` field. Pass this separately from
   * `absPath` when the actual file being processed (absPath) is a temp file
   * that will be deleted right after (e.g. from `record`) -- storing the
   * temp path would leave `drivedb show` pointing at a file that no longer
   * exists. Defaults to `absPath` for the normal `upload` case, where the
   * user's own file stays on disk.
   */
  localPathForDb: string = absPath,
): Promise<void> {
  const fileName = displayName;
  const format = extname(absPath).slice(1).toUpperCase() || "unknown";
  const fileSize = (await stat(absPath)).size;

  console.log(`\n📁 File: ${fileName}`);
  console.log(`   Size: ${formatBytes(fileSize)}`);
  console.log(`   Format: ${format}\n`);

  // --- Step 1: Transcribe ---
  console.log("🎙️  Step 1/2: Transcribing locally...");
  const startTime = Date.now();

  let transcript = "";
  let duration = "unknown";
  let segments: { startMs: number; endMs: number; text: string }[] = [];
  try {
    const result = await transcribe(absPath);
    transcript = result.transcript;
    duration = result.duration;
    segments = result.segments;
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    console.log(`  ✅ Transcription complete (${elapsed}s, duration ≈ ${duration})`);
    if (transcript) {
      const preview = transcript.length > 100 ? transcript.slice(0, 100) + "…" : transcript;
      console.log(`  Preview: "${preview}"`);
    } else {
      console.log("  (no transcript produced — audio may be silent or too short)");
    }
  } catch (err) {
    console.error(`  ❌ Transcription failed: ${(err as Error).message}`);
    console.error("  Continuing with upload anyway (transcript will be empty)...");
  }

  // --- Step 2: Upload to Drive ---
  console.log("\n☁️  Step 2/2: Uploading to Google Drive...");
  const drive = await getDriveClient();
  const mimeType = guessMimeType(absPath);

  const uploadResult = await uploadFile(drive, absPath, fileName, mimeType);
  console.log(`  ✅ Uploaded! Drive link: ${uploadResult.webViewLink}`);

  // --- Step 3: Store in SQLite ---
  const { db } = initDb();
  const record = insertFile(db, {
    driveFileId: uploadResult.fileId,
    driveFileLink: uploadResult.webViewLink,
    localPath: localPathForDb,
    fileName,
    format,
    fileSize,
    duration,
    transcript,
  });

  insertSegments(db, record.id, segments);

  console.log(`\n✅ Record saved!`);
  console.log(`   ID:        ${record.id}`);
  console.log(`   Drive:     ${record.driveFileLink}`);
  console.log(`   Duration:  ${duration}`);
  console.log(`   DB:        ~/.drivedb/drivedb.sqlite3\n`);
}

// ---------------------------------------------------------------------------
// Commands
// ---------------------------------------------------------------------------

async function cmdAuth() {
  console.log("drivedb auth — set up Google Drive OAuth2\n");
  await authenticate();
  console.log("\n✅ Done! You can now use `drivedb upload <file>`.");
}

async function cmdUpload(filePath: string, options: { name?: string }) {
  const absPath = resolve(filePath);

  if (!existsSync(absPath)) {
    console.error(`Error: File not found: ${absPath}`);
    process.exit(1);
  }

  await processAndStoreFile(absPath, options.name || basename(absPath));
}

async function cmdList(options: { tag?: string }) {
  const { db } = initDb();
  const files = options.tag ? listFilesByTag(db, options.tag) : listFiles(db);

  if (files.length === 0) {
    if (options.tag) {
      console.log(`No files with tag "${options.tag}".`);
    } else {
      console.log("No files stored yet. Use `drivedb upload <file>` to add one.");
    }
    return;
  }

  console.log(`\n${files.length} file(s) in drivedb:\n`);

  // Header
  console.log(
    padRight("ID", 5) +
      " " +
      padRight("NAME", 40) +
      " " +
      padRight("FORMAT", 6) +
      " " +
      padRight("SIZE", 10) +
      " " +
      padRight("DURATION", 8) +
      " " +
      padRight("TAGS", 20) +
      " CREATED",
  );
  console.log("-".repeat(100));

  for (const f of files) {
    console.log(
      padRight(String(f.id), 5) +
        " " +
        padRight(f.fileName.length > 38 ? f.fileName.slice(0, 37) + "…" : f.fileName, 40) +
        " " +
        padRight(f.format, 6) +
        " " +
        padRight(formatBytes(f.fileSize), 10) +
        " " +
        padRight(f.duration || "-", 8) +
        " " +
        padRight(f.tags || "-", 20) +
        " " +
        f.createdAt,
    );
  }
  console.log("");
}

async function cmdSearch(query: string) {
  const { db } = initDb();
  const results = searchFiles(db, query);

  if (results.length === 0) {
    console.log(`No results found for: "${query}"`);
    return;
  }

  console.log(`\nFound ${results.length} result(s) for "${query}":\n`);

  for (const r of results) {
    console.log(`  ID ${r.id}: ${r.fileName}`);
    console.log(`    ${r.snippet || "(no transcript preview)"}\n`);
  }
}

async function cmdShow(idStr: string) {
  const id = parseInt(idStr, 10);
  if (isNaN(id)) {
    console.error(`Error: Invalid ID "${idStr}". Must be a number.`);
    process.exit(1);
  }

  const { db } = initDb();
  const record = getFileById(db, id);

  if (!record) {
    console.error(`Error: No record found with ID ${id}.`);
    console.error('Run `drivedb list` to see available records.');
    process.exit(1);
  }

  console.log("\n" + "═".repeat(60));
  console.log(`  ID:        ${record.id}`);
  console.log(`  Name:      ${record.fileName}`);
  console.log(`  Format:    ${record.format}`);
  console.log(`  Size:      ${formatBytes(record.fileSize)}`);
  console.log(`  Duration:  ${record.duration || "unknown"}`);
  console.log(`  Created:   ${record.createdAt}`);
  console.log(`  Local:     ${record.localPath}`);
  console.log(`  Drive ID:  ${record.driveFileId}`);
  console.log(`  Drive URL: ${record.driveFileLink}`);
  console.log(`  Tags:      ${record.tags || "(none)"}`);
  console.log("═".repeat(60));

  if (record.transcript) {
    console.log("\n📝 Transcript:");
    console.log("─".repeat(60));
    console.log(record.transcript);
    console.log("─".repeat(60));
  } else {
    console.log("\n📝 Transcript: (empty)");
  }

  const segs = getSegmentsByFileId(db, id);
  if (segs.length > 0) {
    console.log("\n⏱️  Timestamps:");
    console.log("─".repeat(60));
    for (const seg of segs) {
      console.log(`[${formatMs(seg.startMs)}] ${seg.text}`);
    }
    console.log("─".repeat(60));
  }

  if (record.summary) {
    console.log("\n✨ AI Summary:");
    console.log("─".repeat(60));
    console.log(record.summary);
    console.log("─".repeat(60));
  }
  console.log("");
}

// ---------------------------------------------------------------------------
// Summarize command
// ---------------------------------------------------------------------------

async function cmdSummarize(idStr: string) {
  const id = parseInt(idStr, 10);
  if (isNaN(id)) {
    console.error(`Error: Invalid ID "${idStr}". Must be a number.`);
    process.exit(1);
  }

  const { db } = initDb();
  const record = getFileById(db, id);

  if (!record) {
    console.error(`Error: No record found with ID ${id}.`);
    console.error('Run `drivedb list` to see available records.');
    process.exit(1);
  }

  if (!record.transcript) {
    console.error("Error: No transcript available for this record; nothing to summarize.");
    process.exit(1);
  }

  console.log("\n🤖 Generating summary with Ollama (qwen2.5:7b)...\n");

  try {
    const summaryText = await summarize(record.transcript);
    updateSummary(db, id, summaryText);

    console.log("✨ AI Summary:");
    console.log("─".repeat(60));
    console.log(summaryText);
    console.log("─".repeat(60));
    console.log("");
  } catch (err) {
    console.error(`\n❌ ${(err as Error).message}`);
    process.exit(1);
  }
}

// ---------------------------------------------------------------------------
// Tag command
// ---------------------------------------------------------------------------

async function cmdTag(idStr: string, tagsStr: string) {
  const id = parseInt(idStr, 10);
  if (isNaN(id)) {
    console.error(`Error: Invalid ID "${idStr}". Must be a number.`);
    process.exit(1);
  }

  const { db } = initDb();
  const record = getFileById(db, id);

  if (!record) {
    console.error(`Error: No record found with ID ${id}.`);
    console.error('Run `drivedb list` to see available records.');
    process.exit(1);
  }

  const normalizedTags = tagsStr
    .split(",")
    .map((t) => t.trim())
    .filter((t) => t.length > 0)
    .join(",");

  updateTags(db, id, normalizedTags);

  if (normalizedTags) {
    console.log(`Tags set for ${record.fileName} (ID ${id}): ${normalizedTags}`);
  } else {
    console.log(`Tags cleared for ${record.fileName} (ID ${id}).`);
  }
}

// ---------------------------------------------------------------------------
// Delete command
// ---------------------------------------------------------------------------

async function cmdDelete(idStr: string, options: { force?: boolean }) {
  const id = parseInt(idStr, 10);
  if (isNaN(id)) {
    console.error(`Error: Invalid ID "${idStr}". Must be a number.`);
    process.exit(1);
  }

  const { db } = initDb();
  const record = getFileById(db, id);

  if (!record) {
    console.error(`Error: No record found with ID ${id}.`);
    console.error('Run `drivedb list` to see available records.');
    process.exit(1);
  }

  if (!options.force) {
    console.log(`About to delete: ${record.fileName} (ID ${id})`);
    const rl = createInterface({ input: process.stdin, output: process.stdout });
    const answer = await new Promise<string>((resolve) => {
      rl.question("Delete this record? [y/N] ", resolve);
    });
    rl.close();
    if (answer.toLowerCase() !== "y") {
      console.log("Cancelled.");
      return;
    }
  }

  // Best-effort delete the Drive file — continue with local deletion if it fails.
  try {
    const drive = await getDriveClient();
    await drive.files.delete({ fileId: record.driveFileId });
  } catch (err) {
    console.warn(
      `⚠️  Could not delete Drive file ${record.driveFileId}: ${(err as Error).message}`,
    );
    console.warn("  Continuing with local deletion...");
  }

  deleteFile(db, id);
  console.log(`✅ Deleted: ${record.fileName} (ID ${id})`);
}

// ---------------------------------------------------------------------------
// Play command
// ---------------------------------------------------------------------------

async function cmdPlay(idStr: string) {
  const id = parseInt(idStr, 10);
  if (isNaN(id)) {
    console.error(`Error: Invalid ID "${idStr}". Must be a number.`);
    process.exit(1);
  }

  const { db } = initDb();
  const record = getFileById(db, id);

  if (!record) {
    console.error(`Error: No record found with ID ${id}.`);
    console.error('Run `drivedb list` to see available records.');
    process.exit(1);
  }

  console.log(`Opening: ${record.fileName} (ID ${id})`);
  console.log(`  Link:  ${record.driveFileLink}`);
  execFile("open", [record.driveFileLink]);
}

// ---------------------------------------------------------------------------
// Record command
// ---------------------------------------------------------------------------

async function cmdRecord(options: { name?: string }) {
  console.log("drivedb record — screen + audio capture\n");

  // --- Detect avfoundation devices ---
  const devices = await detectDevices();
  printDeviceSummary(devices);

  // --- Record ---
  let recordedPath: string | null = null;
  try {
    recordedPath = await recordToFile(devices);

    // --- Process through the same pipeline as upload ---
    const displayName = options.name || `recording_${new Date().toISOString().replace(/[:.]/g, "-")}`;
    await processAndStoreFile(recordedPath, displayName, "(recorded — not kept locally, see Drive link)");
  } finally {
    // Clean up the temp recording file.
    if (recordedPath) {
      await cleanupTempFile(recordedPath);
    }
  }
}

// ---------------------------------------------------------------------------
// CLI setup
// ---------------------------------------------------------------------------

const program = new Command();

program
  .name("drivedb")
  .description("Personal video/audio transcriber — upload to Google Drive, transcribe with whisper-cpp, search locally")
  .version(VERSION);

program
  .command("auth")
  .description("Authenticate with Google Drive via OAuth2 (one-time setup)")
  .action(cmdAuth);

program
  .command("upload")
  .description("Upload, transcribe, and index a file")
  .argument("<filePath>", "Path to the audio/video file")
  .option("-n, --name <displayName>", "Custom display name (defaults to filename)")
  .action(cmdUpload);

program
  .command("list")
  .description("List all stored files")
  .option("-t, --tag <tag>", "Filter by tag")
  .action(cmdList);

program
  .command("search")
  .description("Full-text search across transcripts")
  .argument("<query>", "Search query (Thai or English)")
  .action(cmdSearch);

program
  .command("show")
  .description("Show full details and transcript for a record")
  .argument("<id>", "Record ID (from `drivedb list`)")
  .action(cmdShow);

program
  .command("delete")
  .description("Delete a record and its Drive file")
  .argument("<id>", "Record ID (from `drivedb list`)")
  .option("-f, --force", "Skip confirmation prompt")
  .action(cmdDelete);

program
  .command("play")
  .description("Open a recording's Drive link in the browser")
  .argument("<id>", "Record ID (from `drivedb list`)")
  .action(cmdPlay);

program
  .command("summarize")
  .description("Generate an AI summary of a record's transcript via local Ollama")
  .argument("<id>", "Record ID (from `drivedb list`)")
  .action(cmdSummarize);

program
  .command("tag")
  .description("Set comma-separated tags on a record (e.g. \"drivedb tag 5 meeting,thai\")")
  .argument("<id>", "Record ID (from list)")
  .argument("<tags>", "Comma-separated tags")
  .action(cmdTag);

program
  .command("serve")
  .description("Start a local read-only web UI for browsing files, transcripts, and summaries")
  .option("-p, --port <port>", "Port to listen on", "4321")
  .action(async (options: { port: string }) => {
    const port = parseInt(options.port, 10);
    if (isNaN(port)) {
      console.error(`Error: Invalid port "${options.port}". Must be a number.`);
      process.exit(1);
    }
    await startServer(port);
  });

program
  .command("record")
  .description("Record screen + audio, then transcribe and upload")
  .option("-n, --name <displayName>", "Custom display name (defaults to auto-generated timestamp)")
  .action(cmdRecord);

program.parse();
