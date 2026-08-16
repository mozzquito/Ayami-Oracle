/**
 * Generate a Thai-language summary of a transcript using a local Ollama server.
 *
 * Relies on the built-in global fetch (Node >= 18) — no external HTTP client needed.
 */

const OLLAMA_URL = "http://localhost:11434/api/generate";
const MODEL = "qwen2.5:7b";
const TIMEOUT_MS = 120_000;

/**
 * Send a transcript to Ollama and return a concise Thai summary.
 *
 * @throws Error with a user-friendly message if Ollama is unreachable or the
 *         request fails/times out.
 */
export async function summarize(transcript: string): Promise<string> {
  const prompt = [
    `สรุปเนื้อหาต่อไปนี้เป็นภาษาไทยอย่างกระชับ ครอบคลุมประเด็นสำคัญและรายการที่ต้องทำ (action items)`,
    ``,
    `--- เนื้อหา ---`,
    transcript,
    ``,
    `--- สรุป ---`,
  ].join("\n");

  let response: Response;
  try {
    response = await fetch(OLLAMA_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: MODEL, prompt, stream: false }),
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
  } catch (err) {
    throw new Error(
      "Could not reach Ollama at http://localhost:11434. " +
        "Make sure Ollama is installed and running, then try again.",
    );
  }

  if (!response.ok) {
    throw new Error(
      "Could not reach Ollama at http://localhost:11434. " +
        "Make sure Ollama is installed and running, then try again.",
    );
  }

  const data = (await response.json()) as { response?: string };
  return (data.response ?? "").trim();
}
