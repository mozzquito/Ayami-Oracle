import type { ReportData, ClientProfile } from "./types";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
  });
  const body = await res.json();
  if (!res.ok) throw new Error(body.error ?? `request failed: ${res.status}`);
  return body as T;
}

function clientPath(client: string, rest: string): string {
  return `/api/clients/${encodeURIComponent(client)}${rest}`;
}

export const api = {
  schema: () => req<{ schema: string }>("/api/schema"),

  // Client listing & profiles
  listClients: () => req<{ clients: string[] }>("/api/clients"),
  getProfile: (client: string) =>
    req<{ data: ClientProfile }>(clientPath(client, "/profile")),
  saveProfile: (client: string, profile: ClientProfile) =>
    req<{ ok: true }>(clientPath(client, "/profile"), {
      method: "POST",
      body: JSON.stringify(profile),
    }),

  // Month listing & data (client-scoped)
  listMonths: (client: string) =>
    req<{ files: string[] }>(clientPath(client, "/months")),
  loadData: (client: string, file: string) =>
    req<{ data: ReportData }>(clientPath(client, `/data/${file}`)),
  saveData: (client: string, file: string, data: ReportData) =>
    req<{ ok: true }>(clientPath(client, `/data/${file}`), {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // New month with carry-forward
  newMonth: (client: string, file: string, month: string, year: number) =>
    req<{ ok: true; data: ReportData; carried: boolean; prevMonth?: string }>(
      clientPath(client, "/new-month"),
      { method: "POST", body: JSON.stringify({ file, month, year }) },
    ),

  // Generate
  generate: (client: string, file: string) =>
    req<{ ok: true; md: string; docx: string }>(
      clientPath(client, `/generate/${file}`),
      { method: "POST" },
    ),

  // Report preview
  fetchReportMarkdown: (client: string, mdFile: string) =>
    req<{ markdown: string }>(clientPath(client, `/report/${mdFile}`)),

  // Changelog
  changelog: (client: string, file: string) =>
    req<{ changelog: string[]; prevMonth: string | null }>(
      clientPath(client, `/changelog/${file}`),
    ),

  // AI assist (not client-scoped)
  aiAssist: (tool: "zcode" | "agy", prompt: string) =>
    req<{ ok: true; output: string }>("/api/ai-assist", {
      method: "POST",
      body: JSON.stringify({ tool, prompt }),
    }),
};
