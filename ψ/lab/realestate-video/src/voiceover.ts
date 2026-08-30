import type { PipelineConfig, VoiceoverResult } from "./types.js";

// Endpoint, param names, and response shape confirmed from SpeechGen's own
// docs (speechgen.io/en/node/api/) on 2026-08-27 — NOT yet live-tested,
// because SPEECHGEN_EMAIL is still missing (their API requires email + token
// together on every call, not just the token). Two things to verify the
// first time this actually runs:
//   1. Body encoding — the ?r=api/text URL shape is a classic PHP-framework
//      router, which usually means form-urlencoded POST, not JSON. This
//      implementation sends form-urlencoded on that basis; if SpeechGen
//      rejects it, try JSON body instead.
//   2. Thai voice name — SpeechGen's docs didn't list Thai voices by name.
//      DEFAULT_THAI_VOICE below is a placeholder, not a verified value.
//      Check https://speechgen.io/index.php?r=api/voices (or the account's
//      voice picker in the dashboard) for the real Thai voice name and pass
//      it via --voice before trusting this in production.
const SPEECHGEN_ENDPOINT = "https://speechgen.io/index.php?r=api/text";
export const DEFAULT_THAI_VOICE = "REPLACE_WITH_REAL_THAI_VOICE_NAME";

interface SpeechGenResponse {
  status: number;
  file?: string;
  duration?: number;
  cost?: number;
  error?: string;
}

export async function generateVoiceover(
  text: string,
  voice: string = DEFAULT_THAI_VOICE,
  cfg: PipelineConfig
): Promise<VoiceoverResult> {
  if (!cfg.speechgenEmail) {
    throw new Error(
      "speechgenEmail is not set — SpeechGen's API needs the account email alongside the token on every call."
    );
  }
  const body = new URLSearchParams({
    token: cfg.speechgenApiKey,
    email: cfg.speechgenEmail,
    text,
    voice,
    format: "mp3",
  });
  const res = await fetch(SPEECHGEN_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) {
    throw new Error(`SpeechGen ${res.status}: ${await res.text()}`);
  }
  const data = (await res.json()) as SpeechGenResponse;
  if (data.status !== 1 || !data.file) {
    throw new Error(`SpeechGen error: ${data.error ?? JSON.stringify(data)}`);
  }
  return { audioUrl: data.file, durationSec: data.duration ?? 0, costUsd: data.cost };
}
