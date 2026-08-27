import { config } from "./config.js";
import type { EnhancedPhoto } from "./types.js";

// Verified live 2026-08-27: POST https://fal.run/fal-ai/topaz/adjust/image
// with "Authorization: Key <FAL_API_KEY>" is the correct auth scheme (a real
// call returned a normal account-status error, not an auth-format error).
// The account used to verify this needs a credit top-up before real photos
// can be enhanced — see README "Known gaps".
const FAL_ENDPOINT = "https://fal.run/fal-ai/topaz/adjust/image";

interface FalResponse {
  image: { url: string; content_type: string; file_size: number };
}

async function enhanceOne(photoUrl: string): Promise<EnhancedPhoto> {
  try {
    const res = await fetch(FAL_ENDPOINT, {
      method: "POST",
      headers: {
        Authorization: `Key ${config.falApiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        image_url: photoUrl,
        output_format: "jpeg",
        model: "Adjust V2",
      }),
    });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`fal.ai ${res.status}: ${detail}`);
    }
    const data = (await res.json()) as FalResponse;
    return { originalUrl: photoUrl, enhancedUrl: data.image.url, fellBackToOriginal: false };
  } catch (err) {
    // Photo-quality-floor gap flagged by zcode's review: don't let one bad
    // enhancement call kill the whole render — fall back to the original.
    console.warn(`  ⚠ enhancement failed for ${photoUrl}, using original: ${(err as Error).message}`);
    return { originalUrl: photoUrl, enhancedUrl: photoUrl, fellBackToOriginal: true };
  }
}

export async function enhancePhotos(photoUrls: string[]): Promise<EnhancedPhoto[]> {
  return Promise.all(photoUrls.map(enhanceOne));
}
