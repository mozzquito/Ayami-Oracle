/**
 * Local transcription via whisper-cli + ffmpeg.
 *
 * whisper-cli only accepts WAV, so non-WAV files are first converted via ffmpeg.
 * All temp files are cleaned up in a try/finally block.
 */

import { execFile } from "node:child_process";
import { tmpdir } from "node:os";
import { join, extname } from "node:path";
import { unlink, readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

// ---------------------------------------------------------------------------
// Binary paths
// ---------------------------------------------------------------------------

const WHISPER_CLI = "/opt/homebrew/opt/whisper-cpp/bin/whisper-cli";
const WHISPER_MODEL = "~/.local/share/whisper-cpp/models/ggml-medium.bin";
const FFMPEG_BIN = "ffmpeg"; // assume on PATH

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function expandPath(p: string): string {
  if (p.startsWith("~/")) {
    return join(process.env.HOME || "/tmp", p.slice(2));
  }
  return p;
}

/** Check if a file is WAV (16-bit PCM). */
function isWav(filePath: string): boolean {
  return extname(filePath).toLowerCase() === ".wav";
}

// ---------------------------------------------------------------------------
// Transcription
// ---------------------------------------------------------------------------

export interface Segment {
  startMs: number;
  endMs: number;
  text: string;
}

export interface TranscribeResult {
  /** The full transcript text. */
  transcript: string;
  /** Approximate duration string (e.g. "12:34"). */
  duration: string;
  /** Timestamped transcript segments (from whisper-cli TSV output). */
  segments: Segment[];
}

/**
 * Transcribe an audio/video file using whisper-cli.
 *
 * If the file is not WAV, it will first be converted via ffmpeg.
 * Temp files are always cleaned up.
 */
export async function transcribe(filePath: string): Promise<TranscribeResult> {
  const modelPath = expandPath(WHISPER_MODEL);

  if (!existsSync(WHISPER_CLI)) {
    throw new Error(
      `whisper-cli not found at ${WHISPER_CLI}. Install via: brew install whisper-cpp`,
    );
  }

  if (!existsSync(modelPath)) {
    throw new Error(
      `Whisper model not found at ${modelPath}. Download from https://huggingface.co/ggerganov/whisper.cpp`,
    );
  }

  const tempDir = tmpdir();
  let wavPath: string | null = null;
  let whisperOutputBase: string | null = null;
  const inputPath = filePath;

  try {
    // --- Step 1: Convert to WAV if needed ---
    if (!isWav(filePath)) {
      wavPath = join(tempDir, `drivedb_${Date.now()}.wav`);
      console.log(`  Converting to WAV: ${wavPath}`);
      await execFileAsync(FFMPEG_BIN, [
        "-i",
        inputPath,
        "-ar",
        "16000", // 16 kHz — whisper's expected sample rate
        "-ac",
        "1", // mono
        "-c:a",
        "pcm_s16le", // 16-bit PCM
        "-y", // overwrite
        wavPath,
      ]);
    } else {
      wavPath = inputPath;
    }

    // --- Step 2: Run whisper-cli ---
    const outputBase = join(tempDir, `drivedb_whisper_${Date.now()}`);
    whisperOutputBase = outputBase;
    console.log("  Transcribing with whisper-cli (medium model)...");
    console.log("  (this may take a while depending on file length)");

    await execFileAsync(WHISPER_CLI, [
      "-m", modelPath,
      "-f", wavPath,
      "-otxt", // plain text output
      "-ocsv", // CSV timestamps (this whisper-cli build has no -otsv/TSV flag)
      "-of", outputBase, // output file base name
      // No -l flag — auto-detect language (works for Thai, English, mixed)
    ], {
      timeout: 60 * 60 * 1000, // 1 hour max
    });

    // Read the .txt output
    const txtPath = `${outputBase}.txt`;
    let transcript = "";
    try {
      transcript = (await readFile(txtPath, "utf-8")).trim();
    } catch {
      console.warn("  Warning: whisper-cli did not produce a .txt output file.");
    }

    // Read and parse the .csv output for timestamped segments
    const segments = await parseCsvSegments(`${outputBase}.csv`);

    // --- Step 3: Estimate duration ---
    const duration = await estimateDuration(wavPath);

    return { transcript, duration, segments };
  } finally {
    // --- Cleanup temp files ---
    if (wavPath && wavPath !== inputPath && existsSync(wavPath)) {
      try {
        await unlink(wavPath);
      } catch {
        // best-effort cleanup
      }
    }
    if (whisperOutputBase) {
      for (const ext of [".txt", ".csv"]) {
        const p = `${whisperOutputBase}${ext}`;
        if (existsSync(p)) {
          try {
            await unlink(p);
          } catch {
            // best-effort cleanup
          }
        }
      }
    }
  }
}

/**
 * Parse whisper-cli CSV output (start,end,text — text is quoted and may
 * contain embedded commas) into an array of Segment objects.
 *
 * Returns an empty array if the file is missing or cannot be parsed.
 */
async function parseCsvSegments(csvPath: string): Promise<Segment[]> {
  try {
    const raw = (await readFile(csvPath, "utf-8")).trim();
    const lines = raw.split("\n");
    // Skip header row (start,end,text)
    const segments: Segment[] = [];
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;

      const firstComma = line.indexOf(",");
      if (firstComma === -1) continue;
      const startMs = parseInt(line.slice(0, firstComma), 10);

      const rest = line.slice(firstComma + 1);
      const secondComma = rest.indexOf(",");
      if (secondComma === -1) continue;
      const endMs = parseInt(rest.slice(0, secondComma), 10);

      let text = rest.slice(secondComma + 1);
      if (text.startsWith('"') && text.endsWith('"')) {
        text = text.slice(1, -1).replace(/""/g, '"');
      }
      text = text.trimStart();

      if (isNaN(startMs) || isNaN(endMs)) continue;
      segments.push({ startMs, endMs, text });
    }
    return segments;
  } catch {
    return [];
  }
}

/**
 * Estimate duration of an audio file using ffprobe (or fall back to a
 * reasonable default).
 */
async function estimateDuration(audioPath: string): Promise<string> {
  try {
    const { stdout } = await execFileAsync("ffprobe", [
      "-v",
      "error",
      "-show_entries",
      "format=duration",
      "-of",
      "default=noprint_wrappers=1:nokey=1",
      audioPath,
    ]);
    const seconds = Math.round(parseFloat(stdout.trim()));
    if (isNaN(seconds) || seconds < 0) return "unknown";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins >= 60) {
      const hrs = Math.floor(mins / 60);
      const remMins = mins % 60;
      return `${hrs}:${String(remMins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
    }
    return `${mins}:${String(secs).padStart(2, "0")}`;
  } catch {
    return "unknown";
  }
}

/**
 * Guess MIME type from file extension.
 */
export function guessMimeType(filePath: string): string {
  const ext = extname(filePath).toLowerCase();
  const mimeMap: Record<string, string> = {
    ".mp4": "video/mp4",
    ".mkv": "video/x-matroska",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".wmv": "video/x-ms-wmv",
    ".flv": "video/x-flv",
    ".webm": "video/webm",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".aac": "audio/aac",
    ".wma": "audio/x-ms-wma",
    ".opus": "audio/opus",
  };
  return mimeMap[ext] || "application/octet-stream";
}
