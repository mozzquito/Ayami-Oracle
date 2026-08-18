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
export async function summarize(
  transcript: string,
  timeoutMs: number = TIMEOUT_MS,
  keepAlive?: number,
): Promise<string> {
  const prompt = [
    `สรุปเนื้อหาต่อไปนี้เป็นภาษาไทยอย่างกระชับ ครอบคลุมประเด็นสำคัญและรายการที่ต้องทำ (action items)`,
    ``,
    `--- เนื้อหา ---`,
    transcript,
    ``,
    `--- สรุป ---`,
  ].join("\n");

  const body: { model: string; prompt: string; stream: boolean; keep_alive?: number } = {
    model: MODEL,
    prompt,
    stream: false,
  };
  // Pass keep_alive to tell Ollama how long to keep the model resident in
  // (GPU) memory after this request. Passing 0 unloads it immediately --
  // used by the auto-summarize path so a subsequent whisper-cli invocation
  // doesn't fail with an out-of-memory error competing for GPU memory with
  // an idle-but-still-loaded Ollama model (confirmed reproducible on this
  // machine: whisper's medium model + qwen2.5:7b together exceed available
  // GPU memory). Manual `drivedb summarize` calls omit this, leaving
  // Ollama's own default keep-alive in place (useful when summarizing
  // several records back-to-back).
  if (keepAlive !== undefined) {
    body.keep_alive = keepAlive;
  }

  let response: Response;
  try {
    response = await fetch(OLLAMA_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(timeoutMs),
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
