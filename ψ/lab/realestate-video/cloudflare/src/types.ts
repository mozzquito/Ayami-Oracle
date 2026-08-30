export interface Env {
  DB: D1Database;
  PIPELINE: Workflow;
  OPENROUTER_API_KEY: string;
  FAL_API_KEY: string;
  SPEECHGEN_API_KEY: string;
  SPEECHGEN_EMAIL?: string;
  CREATOMATE_API_KEY: string;
}
