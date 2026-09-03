import type { PipelineConfig, VoiceoverResult } from "./types.js";

// Endpoint, param names, and response shape confirmed from SpeechGen's own
// docs (speechgen.io/en/node/api/) on 2026-08-27 — the text-to-speech call
// itself is still NOT live-tested (blocked on SPEECHGEN_EMAIL). One thing
// still unverified:
//   - Body encoding — the ?r=api/text URL shape is a classic PHP-framework
//     router, which usually means form-urlencoded POST, not JSON. This
//     implementation sends form-urlencoded on that basis; if SpeechGen
//     rejects it, try JSON body instead.
//
// Thai voice name VERIFIED live 2026-08-31 — POST to
// https://speechgen.io/index.php?r=api/voices with just the token (no email
// needed for this endpoint) returned a real "Thai" voice list. "Achara" is
// the cheapest (cpm 1000, "pro" tier) dedicated Thai female voice; the rest
// are generic multi-language "hd" voices with a "TH" suffix. Not yet
// confirmed how it actually sounds — only that the name is real and won't
// 404/error on the text-to-speech call for that reason.
const SPEECHGEN_ENDPOINT = "https://speechgen.io/index.php?r=api/text";
export const DEFAULT_THAI_VOICE = "Achara";

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
