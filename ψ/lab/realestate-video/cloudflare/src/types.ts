export interface Env {
  DB: D1Database;
  PIPELINE: Workflow;
  OPENROUTER_API_KEY: string;
  CLOUDFLARE_API_TOKEN: string;
  CLOUDFLARE_ACCOUNT_ID: string;
  SPEECHGEN_API_KEY: string;
  SPEECHGEN_EMAIL?: string;
  CREATOMATE_API_KEY: string;
}
