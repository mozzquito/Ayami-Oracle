/**
 * Screen + audio recording via ffmpeg (macOS avfoundation).
 *
 * Detects screen capture device, microphone, and optionally BlackHole
 * (system audio loopback) at runtime by parsing ffmpeg's stderr output.
 * Records to a temp MP4 file; caller is responsible for cleanup.
 */

import { spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { unlink } from "node:fs/promises";
import { existsSync } from "node:fs";
import { promisify } from "node:util";
import { execFile } from "node:child_process";

const execFileAsync = promisify(execFile);

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface DetectedDevices {
  screenIndex: number;
  micIndex: number;
  blackholeIndex: number | null;
}

// ---------------------------------------------------------------------------
// Device detection
// ---------------------------------------------------------------------------

/**
 * Detect avfoundation devices by running `ffmpeg -f avfoundation -list_devices true -i ""`.
 *
 * This command intentionally errors after printing the device list to stderr —
 * that's expected ffmpeg behaviour, not a failure.
 */
export async function detectDevices(): Promise<DetectedDevices> {
  let screenIndex = -1;
  let micIndex = -1;
  let blackholeIndex: number | null = null;

  try {
    // The command always exits non-zero (ffmpeg expects a real input).
    // We intentionally use execFile so we can capture stderr.
    const { stderr } = await execFileAsync(
      "ffmpeg",
      ["-f", "avfoundation", "-list_devices", "true", "-i", ""],
      { timeout: 10_000 },
    );

    parseDeviceList(stderr, (type, index, name) => {
      if (type === "video" && /capture\s+screen/i.test(name)) {
        screenIndex = index;
      }
      if (type === "audio" && /microphone/i.test(name) && micIndex === -1) {
        micIndex = index;
      }
      if (type === "audio" && /blackhole/i.test(name) && blackholeIndex === null) {
        blackholeIndex = index;
      }
    });
  } catch (err: any) {
    // ffmpeg exits with code 1 for device listing — that's normal.
    // The useful output is on stderr, which we already parsed above
    // via the promise rejection path.
    if (err.stderr) {
      parseDeviceList(err.stderr, (type, index, name) => {
        if (type === "video" && /capture\s+screen/i.test(name)) {
          screenIndex = index;
        }
        if (type === "audio" && /microphone/i.test(name) && micIndex === -1) {
          micIndex = index;
        }
        if (type === "audio" && /blackhole/i.test(name) && blackholeIndex === null) {
          blackholeIndex = index;
        }
      });
    }
  }

  if (screenIndex === -1) {
    throw new Error(
      "No screen capture device found (expected a device name containing 'Capture screen'). " +
        "Make sure you're running on macOS.",
    );
  }

  if (micIndex === -1) {
    throw new Error(
      "No microphone device found (expected a device name containing 'Microphone').",
    );
  }

  return { screenIndex, micIndex, blackholeIndex };
}

/**
 * Parse ffmpeg avfoundation device list from stderr.
 *
 * ffmpeg prefixes each device line with an indev log tag like
 *   [AVFoundation indev @ 0x...] [0] FaceTime HD Camera
 * so we match the LAST occurrence of "[index] name" on the line
 * (the device index/name pair is always the last bracketed block).
 *
 * Example stderr:
 *   [AVFoundation indev @ 0x876c18140] AVFoundation video devices:
 *   [AVFoundation indev @ 0x876c18140] [0] FaceTime HD Camera
 *   [AVFoundation indev @ 0x876c18140] [1] Capture screen 0
 *   [AVFoundation indev @ 0x876c18140] AVFoundation audio devices:
 *   [AVFoundation indev @ 0x876c18140] [0] MacBook Pro Microphone
 *   [AVFoundation indev @ 0x876c18140] [1] Microsoft Teams Audio
 */
function parseDeviceList(
  stderr: string,
  onDevice: (type: "video" | "audio", index: number, name: string) => void,
): void {
  let currentSection: "video" | "audio" | "unknown" = "unknown";

  for (const line of stderr.split("\n")) {
    if (/AVFoundation\s+video\s+devices/i.test(line)) {
      currentSection = "video";
      continue;
    }
    if (/AVFoundation\s+audio\s+devices/i.test(line)) {
      currentSection = "audio";
      continue;
    }

    // Match device lines: look for the last "[N] Name" pattern on the line.
    // Handles both bare "[0] Name" and prefixed "[AVFoundation indev @ ...] [0] Name".
    const allMatches = [...line.matchAll(/\[(\d+)\]\s+(.+)$/g)];
    const lastMatch = allMatches[allMatches.length - 1];
    if (lastMatch && currentSection !== "unknown") {
      const index = parseInt(lastMatch[1], 10);
      const name = lastMatch[2].trim();
      onDevice(currentSection, index, name);
    }
  }
}

// ---------------------------------------------------------------------------
// Recording
// ---------------------------------------------------------------------------

/**
 * Record screen + audio to a temp MP4 file.
 *
 * Returns the path to the recorded file. The caller is responsible for
 * deleting it after processing.
 *
 * When BlackHole is available, captures both microphone and system audio
 * using two avfoundation inputs mixed via amix.
 *
 * When BlackHole is NOT available, captures screen + microphone only
 * and prints a one-time suggestion about installing BlackHole.
 */
export async function recordToFile(devices: DetectedDevices): Promise<string> {
  const outputPath = join(tmpdir(), `drivedb_record_${Date.now()}.mp4`);

  const args: string[] = [];

  // NOTE: an explicit "-framerate 30" input flag was tried here and removed
  // -- it made things worse (tested: produced a wildly short/inaccurate
  // output duration, e.g. 0.5s of content for a 5s capture). avfoundation's
  // own default rate negotiation works better left alone; the real fix for
  // choppiness is the hardware encoder below.

  if (devices.blackholeIndex !== null) {
    // --- Two-input capture: screen+mic + BlackHole system audio ---
    // Input 0: video from screen, audio from mic
    args.push("-f", "avfoundation", "-i", `${devices.screenIndex}:${devices.micIndex}`);
    // Input 1: audio-only from BlackHole (no video — "none")
    args.push("-f", "avfoundation", "-i", `none:${devices.blackholeIndex}`);
    // Mix the two audio streams together
    args.push(
      "-filter_complex",
      "[0:a][1:a]amix=inputs=2:duration=longest[aout]",
    );
    // Map video from input 0, audio from the mix
    args.push("-map", "0:v", "-map", "[aout]");
  } else {
    // --- Single-input capture: screen + mic only ---
    args.push("-f", "avfoundation", "-i", `${devices.screenIndex}:${devices.micIndex}`);
  }

  // Downscale the capture. On a Retina display, avfoundation's native
  // screen resolution (e.g. 2560x1600) is heavy for the whole real-time
  // pipeline -- capture + encode -- to keep pace with, even on hardware
  // encoding. 1280px wide is plenty for a personal screen recording and
  // meaningfully reduces load (and upload size). "-2" keeps the height
  // even and preserves aspect ratio.
  args.push("-vf", "scale=1280:-2");

  // Encode video with Apple's hardware encoder (VideoToolbox) instead of
  // software libx264. At screen-capture resolutions, real-time software
  // encoding routinely can't keep up (ffmpeg logs an explicit "MB rate >
  // level limit" warning when this happens) -- the encoder falls behind,
  // and since audio/video share the same ffmpeg process and clock, the
  // audio comes out choppy along with the dropped video frames.
  //
  // "-realtime true" explicitly hints VideoToolbox to prioritize keeping
  // up with real-time input over maximizing compression quality/efficiency
  // -- without it, encode speed ramps up slowly from ~0.4x over the first
  // few seconds; with it, measured speed stays consistently at 0.95-1.0x
  // from near the start.
  args.push("-c:v", "h264_videotoolbox", "-realtime", "true", "-c:a", "aac");

  // Output settings
  args.push("-y", outputPath);

  console.log(`\n🔴 Recording to: ${outputPath}`);
  console.log("   Press Enter (or Ctrl+C) to stop...\n");

  const child = spawn("ffmpeg", args, {
    stdio: ["pipe", "pipe", "pipe"],
  });

  // Pipe ffmpeg stderr through to the user so they can see any errors.
  if (child.stderr) {
    child.stderr.on("data", (chunk: Buffer) => {
      // ffmpeg writes progress info to stderr; let it through at low verbosity.
      process.stderr.write(chunk);
    });
  }

  // Wait for the user to press Enter OR Ctrl+C to stop recording.
  //
  // Ctrl+C sends SIGINT to this whole process, and Node's default behaviour
  // (with no listener) is to exit immediately -- which would kill drivedb
  // before it ever gets to transcribe/upload the file, leaving a valid but
  // orphaned recording in the temp dir. Intercepting SIGINT here lets both
  // "stop keys" converge on the same graceful ffmpeg shutdown + processing
  // pipeline. A second Ctrl+C (for an impatient user) force-exits for real.
  const rl = createInterface({ input: process.stdin });
  const onSigint = () => {
    // Second Ctrl+C: user really wants out. Let Node's default SIGINT
    // behaviour take over instead of hanging forever waiting on ffmpeg.
    process.exit(130);
  };
  const stopPromise = new Promise<void>((resolve) => {
    const stop = () => {
      console.log("\n  Stopping recording...");
      // Swap to the force-exit handler now that the first stop signal has
      // been received -- a second Ctrl+C during ffmpeg shutdown should abort
      // immediately rather than trigger this same graceful path twice.
      process.off("SIGINT", stop);
      process.on("SIGINT", onSigint);
      resolve();
    };
    rl.on("line", stop);
    process.on("SIGINT", stop);
  });

  await stopPromise;
  rl.close();

  // Gracefully stop ffmpeg: send 'q' to its stdin. This signals ffmpeg to
  // finish writing the current frame and exit cleanly (properly finalizing
  // the MP4 container / moov atom). SIGINT also works but 'q' is the
  // standard ffmpeg interactive quit command and produces cleaner output.
  if (child.stdin && !child.stdin.destroyed) {
    child.stdin.write("q");
  }

  // Wait for ffmpeg to actually exit so the file is finalized.
  const exitCode = await new Promise<number | null>((resolve) => {
    child.on("close", resolve);
  });

  // ffmpeg has exited -- restore normal Ctrl+C behaviour for the rest of the
  // command (transcribe/upload), rather than leaving our force-exit-on-second-
  // signal handler registered for phases it was never meant to cover.
  process.off("SIGINT", onSigint);

  if (exitCode !== null && exitCode !== 0) {
    // exitCode 0 = clean finish; non-zero after 'q' is normal for some builds
    // (ffmpeg may exit 1 even on clean 'q' shutdown in certain configs).
    // Only warn if the output file doesn't exist.
    if (!existsSync(outputPath)) {
      throw new Error(
        `ffmpeg exited with code ${exitCode} and output file was not created.`,
      );
    }
  }

  return outputPath;
}

/**
 * Print detected devices and, if BlackHole is missing, a one-time suggestion.
 */
export function printDeviceSummary(devices: DetectedDevices): void {
  console.log(`📹 Screen capture: device [${devices.screenIndex}]`);
  console.log(`🎤 Microphone:     device [${devices.micIndex}]`);

  if (devices.blackholeIndex !== null) {
    console.log(`🔊 System audio:   device [${devices.blackholeIndex}] (BlackHole)`);
  } else {
    console.log("🔇 System audio:   not available (no BlackHole device detected)\n");
    console.log(
      "💡 To capture system audio (e.g. browser tab sound, music), install BlackHole —\n" +
        "   a free, open-source virtual audio loopback driver:\n" +
        "     brew install blackhole-2ch\n" +
        "   Then create a Multi-Output Device in Audio MIDI Setup that includes both\n" +
        "   your speakers and BlackHole, so you can still hear audio while it's captured.\n" +
        "   See https://github.com/ExistentialAudio/BlackHole for setup details.",
    );
  }
}

/**
 * Clean up a temp recording file (best-effort).
 */
export async function cleanupTempFile(filePath: string): Promise<void> {
  try {
    if (existsSync(filePath)) {
      await unlink(filePath);
    }
  } catch {
    // best-effort cleanup — same pattern as transcribe.ts
  }
}
