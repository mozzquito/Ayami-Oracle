import type { PropertyInput } from "../../src/types.js";
import type { Env } from "./types.js";

export { RealEstateVideoWorkflow } from "./workflow.js";

function badRequest(message: string): Response {
  return Response.json({ error: message }, { status: 400 });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "POST" && url.pathname === "/jobs") {
      let input: PropertyInput;
      try {
        input = (await request.json()) as PropertyInput;
      } catch {
        return badRequest("body must be JSON");
      }
      if (
        !Array.isArray(input.photoUrls) ||
        input.photoUrls.length === 0 ||
        !input.price ||
        !input.location ||
        !input.agentName ||
        !input.agentPhone
      ) {
        return badRequest("required: photoUrls[], price, location, agentName, agentPhone");
      }

      const jobId = crypto.randomUUID();
      await env.DB.prepare("INSERT INTO jobs (id, status, input_json) VALUES (?, 'pending', ?)")
        .bind(jobId, JSON.stringify(input))
        .run();
      await env.PIPELINE.create({ id: jobId, params: { jobId, input } });

      return Response.json({ jobId, status: "pending" }, { status: 202 });
    }

    const jobMatch = url.pathname.match(/^\/jobs\/([^/]+)$/);
    if (request.method === "GET" && jobMatch) {
      const row = await env.DB.prepare("SELECT * FROM jobs WHERE id = ?").bind(jobMatch[1]).first();
      if (!row) return Response.json({ error: "not found" }, { status: 404 });
      return Response.json(row);
    }

    return new Response("Not found", { status: 404 });
  },
};
