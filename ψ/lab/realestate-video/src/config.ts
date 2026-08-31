import "dotenv/config";
import type { PipelineConfig } from "./types.js";

function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(
      `Missing ${name} in .env — run scripts/setup-wizard.sh to fill it in.`
    );
  }
  return value;
}

function optional(name: string): string | undefined {
  return process.env[name] || undefined;
}

/** CLI entry point only — reads from process.env/.env. The Cloudflare Worker
 * builds a PipelineConfig directly from its `env` bindings instead (there is
 * no process.env in the Workers runtime). */
export function loadConfig(): PipelineConfig {
  return {
    openrouterApiKey: required("OPENROUTER_API_KEY"),
    cloudflareApiToken: required("CLOUDFLARE_API_TOKEN"),
    cloudflareAccountId: required("CLOUDFLARE_ACCOUNT_ID"),
    speechgenApiKey: required("SPEECHGEN_API_KEY"),
    // Not resolved yet as of 2026-08-27, see README "Known gaps".
    speechgenEmail: optional("SPEECHGEN_EMAIL"),
    creatomateApiKey: required("CREATOMATE_API_KEY"),
  };
}
