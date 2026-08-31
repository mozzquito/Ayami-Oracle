export interface PropertyInput {
  /** Publicly accessible photo URLs (5-8 recommended). Prototype does not host uploads yet. */
  photoUrls: string[];
  price: string;
  location: string;
  btsStation?: string;
  sqm?: string;
  bedrooms?: string;
  extraHighlights?: string;
  agentName: string;
  agentPhone: string;
  agentLineId?: string;
}

export interface EnhancedPhoto {
  originalUrl: string;
  enhancedUrl: string;
  /** true if enhancement failed and we fell back to the original photo */
  fellBackToOriginal: boolean;
}

export interface VoiceoverResult {
  audioUrl: string;
  durationSec: number;
  costUsd?: number;
}

export interface RenderResult {
  videoUrl: string;
  renderId: string;
  widthPx: number;
  heightPx: number;
  fileSizeBytes: number;
}

export interface PipelineConfig {
  openrouterApiKey: string;
  /** Cloudflare API Token with Workers AI run permission — used for photo enhancement
   * (pruna/p-image-upscale). Replaces fal.ai as of 2026-08-31 (fal.ai account locked,
   * needs a credit top-up — see README "Known gaps"). */
  cloudflareApiToken: string;
  cloudflareAccountId: string;
  speechgenApiKey: string;
  /** SpeechGen's API requires the account email alongside the token on every call. */
  speechgenEmail?: string;
  creatomateApiKey: string;
}
