import { readFileSync } from "node:fs";
import { basename } from "node:path";

// Read lazily (inside functions), not as module-level constants — dotenv's
// loadEnv() runs in cli.ts's own body, which executes AFTER all of cli.ts's
// static imports (including this module) are already evaluated. A
// module-level `const X = process.env.X` here would permanently capture an
// empty value from before .env was ever loaded. Confirmed as a real bug
// 2026-08-23: a live `daily` run silently skipped Discord delivery because
// of exactly this, even with DISCORD_WEBHOOK_URL correctly set in .env.
function webhookUrl(): string {
  return process.env.DISCORD_WEBHOOK_URL ?? "";
}

// Discord webhook file-upload cap (non-boosted server default). Configurable
// in case the target server has boost-raised limits.
function maxUploadBytes(): number {
  return Number(process.env.DISCORD_MAX_UPLOAD_BYTES ?? 25 * 1024 * 1024);
}

export class DiscordUploadTooLargeError extends Error {
  byteLength: number;
  constructor(byteLength: number, capBytes: number) {
    super(`Report file is ${(byteLength / 1024 / 1024).toFixed(1)}MB, exceeds the ${(capBytes / 1024 / 1024).toFixed(0)}MB Discord upload cap`);
    this.byteLength = byteLength;
  }
}

export function hasDiscordWebhook(): boolean {
  return Boolean(webhookUrl());
}

/** Throws DiscordUploadTooLargeError if the file exceeds the configured cap — caller decides the fallback. */
export async function sendReportFile(filePath: string, content: string): Promise<void> {
  const url = webhookUrl();
  if (!url) {
    console.log("DISCORD_WEBHOOK_URL not set — skipping Discord delivery.");
    return;
  }

  const bytes = readFileSync(filePath);
  const cap = maxUploadBytes();
  if (bytes.byteLength > cap) {
    throw new DiscordUploadTooLargeError(bytes.byteLength, cap);
  }

  const form = new FormData();
  form.append("payload_json", JSON.stringify({ content }));
  form.append("files[0]", new Blob([bytes], { type: "text/html" }), basename(filePath));

  const res = await fetch(url, { method: "POST", body: form });
  if (!res.ok) {
    throw new Error(`Discord webhook POST failed: HTTP ${res.status} — ${await res.text()}`);
  }
}

/** Text-only message, e.g. a run-failure or oversize-fallback notice. Never throws — logs and swallows so it can't mask the real error it's reporting. */
export async function sendTextAlert(content: string): Promise<void> {
  const url = webhookUrl();
  if (!url) return;
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ content }),
    });
    if (!res.ok) console.error(`Discord alert POST failed: HTTP ${res.status} — ${await res.text()}`);
  } catch (err) {
    console.error(`Discord alert POST failed: ${(err as Error).message}`);
  }
}
