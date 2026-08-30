import type { EnhancedPhoto, PipelineConfig, RenderResult, VoiceoverResult } from "./types.js";

// Fully verified live 2026-08-27 against the real Creatomate API:
//   - POST /v1/renders with {source:{output_format,width,height,duration,elements}}
//     returns 202 + an array with {id, status:"planned", url}
//   - GET /v1/renders/{id} returns {id, status, url, width, height,
//     frame_rate, duration, file_size} once done
//   - element type "text" (text, width, height, y, fill_color) — verified
//   - element type "image" (source, width, height, fit:"cover") — verified,
//     including with a Thai-text sibling element in the same render
// NOT verified this session: multiple images auto-sequenced on a shared
// "track" (only ever rendered one image at a time in testing), and the
// "audio" element type. Both follow Creatomate's documented pattern below,
// but confirm with a real multi-photo run before trusting this for a paying
// customer — see README "Known gaps".
//
// Also observed on every test render: `render_scale` came back as 0.25
// (270x480 instead of the requested 1080x1920) regardless of what was
// requested — this looks like a trial-account preview cap, not something
// this code controls. Check Creatomate's billing/plan page before promising
// full-resolution output to a customer.
const CREATOMATE_BASE = "https://api.creatomate.com/v1";
const POLL_INTERVAL_MS = 3000;
const MAX_POLLS = 40; // ~2 minutes ceiling — fail loudly instead of hanging forever

interface CreatomateCreateResponse {
  id: string;
  status: string;
  url: string;
}

interface CreatomateStatusResponse {
  id: string;
  status: "planned" | "waiting" | "transcoding" | "succeeded" | "failed";
  url?: string;
  width?: number;
  height?: number;
  file_size?: number;
  error_message?: string;
}

function buildSource(
  photos: EnhancedPhoto[],
  voiceover: VoiceoverResult,
  agentName: string,
  agentPhone: string
) {
  const perPhotoDuration = voiceover.durationSec / photos.length;
  const imageElements = photos.map((p) => ({
    type: "image",
    track: 1,
    source: p.enhancedUrl,
    duration: perPhotoDuration,
    width: "100%",
    height: "100%",
    fit: "cover",
  }));

  return {
    output_format: "mp4",
    width: 1080,
    height: 1920,
    duration: voiceover.durationSec,
    elements: [
      ...imageElements,
      {
        type: "audio",
        track: 2,
        source: voiceover.audioUrl,
      },
      {
        type: "text",
        track: 3,
        text: `${agentName}  |  ${agentPhone}`,
        width: "90%",
        height: "10%",
        x: "50%",
        y: "92%",
        x_alignment: "50%",
        fill_color: "#ffffff",
        background_color: "rgba(0,0,0,0.55)",
      },
    ],
  };
}

async function pollUntilDone(id: string, cfg: PipelineConfig): Promise<CreatomateStatusResponse> {
  for (let i = 0; i < MAX_POLLS; i++) {
    await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
    const res = await fetch(`${CREATOMATE_BASE}/renders/${id}`, {
      headers: { Authorization: `Bearer ${cfg.creatomateApiKey}` },
    });
    if (!res.ok) throw new Error(`Creatomate poll ${res.status}: ${await res.text()}`);
    const data = (await res.json()) as CreatomateStatusResponse;
    if (data.status === "succeeded" || data.status === "failed") return data;
  }
  throw new Error(`Creatomate render ${id} did not finish within ${MAX_POLLS * POLL_INTERVAL_MS}ms`);
}

export async function renderVideo(
  photos: EnhancedPhoto[],
  voiceover: VoiceoverResult,
  agentName: string,
  agentPhone: string,
  cfg: PipelineConfig
): Promise<RenderResult> {
  const source = buildSource(photos, voiceover, agentName, agentPhone);
  const res = await fetch(`${CREATOMATE_BASE}/renders`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${cfg.creatomateApiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ source }),
  });
  if (!res.ok) throw new Error(`Creatomate create ${res.status}: ${await res.text()}`);
  const [created] = (await res.json()) as CreatomateCreateResponse[];

  const done = await pollUntilDone(created.id, cfg);
  if (done.status === "failed" || !done.url) {
    throw new Error(`Creatomate render failed: ${done.error_message ?? "unknown error"}`);
  }
  return {
    videoUrl: done.url,
    renderId: done.id,
    widthPx: done.width ?? 0,
    heightPx: done.height ?? 0,
    fileSizeBytes: done.file_size ?? 0,
  };
}
