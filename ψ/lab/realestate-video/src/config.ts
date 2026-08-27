import "dotenv/config";

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

export const config = {
  openrouterApiKey: required("OPENROUTER_API_KEY"),
  falApiKey: required("FAL_API_KEY"),
  speechgenApiKey: required("SPEECHGEN_API_KEY"),
  // SpeechGen's API requires the account email alongside the token on every
  // call — not resolved yet as of 2026-08-27, see README "Known gaps".
  speechgenEmail: optional("SPEECHGEN_EMAIL"),
  creatomateApiKey: required("CREATOMATE_API_KEY"),
};
