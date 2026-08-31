import type { EnhancedPhoto, PipelineConfig } from "./types.js";

// Switched from fal.ai to Cloudflare Workers AI 2026-08-31 — fal.ai's account
// used during the original build got locked (403 User is locked. Reason:
// TOP_UP) and was never actually verified end-to-end (see git history for the
// old implementation). This swap is NOT yet live-tested either — same
// "verified live" bar as the rest of this pipeline once a real call succeeds.
//
// Model: pruna/p-image-upscale (docs: developers.cloudflare.com/ai/models/pruna/p-image-upscale/).
// It's an upscaler, not a pure "adjust lighting/color" model like fal.ai's
// Adjust V2 was — enhance_details is the closest available lever. target=4
// (megapixels) is the model's own default; real-estate phone photos are
// typically already >=4MP, so this may end up resizing rather than
// "upscaling" in practice. Revisit if output quality looks worse than the
// original, not just different.
//
// Response envelope assumed to be Cloudflare's standard REST wrapper
// ({ result: { image: <url> }, success, errors }) per the model's documented
// output shape (a presigned URL string) — NOT confirmed against a real
// response yet.
const WORKERS_AI_MODEL = "pruna/p-image-upscale";

interface WorkersAiUpscaleResponse {
  result?: { image?: string };
  success: boolean;
  errors?: { code: number; message: string }[];
}

async function enhanceOne(photoUrl: string, cfg: PipelineConfig): Promise<EnhancedPhoto> {
  try {
    const res = await fetch(
      `https://api.cloudflare.com/client/v4/accounts/${cfg.cloudflareAccountId}/ai/run`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${cfg.cloudflareApiToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: WORKERS_AI_MODEL,
          input: {
            image: photoUrl,
            target: 4,
            enhance_details: true,
            output_format: "jpg",
          },
        }),
      }
    );
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`Workers AI ${res.status}: ${detail}`);
    }
    const data = (await res.json()) as WorkersAiUpscaleResponse;
    if (!data.success || !data.result?.image) {
      throw new Error(`Workers AI error: ${JSON.stringify(data.errors ?? data)}`);
    }
    return { originalUrl: photoUrl, enhancedUrl: data.result.image, fellBackToOriginal: false };
  } catch (err) {
    // Photo-quality-floor gap flagged by zcode's review: don't let one bad
    // enhancement call kill the whole render — fall back to the original.
    console.warn(`  ⚠ enhancement failed for ${photoUrl}, using original: ${(err as Error).message}`);
    return { originalUrl: photoUrl, enhancedUrl: photoUrl, fellBackToOriginal: true };
  }
}

export async function enhancePhotos(photoUrls: string[], cfg: PipelineConfig): Promise<EnhancedPhoto[]> {
  return Promise.all(photoUrls.map((url) => enhanceOne(url, cfg)));
}
