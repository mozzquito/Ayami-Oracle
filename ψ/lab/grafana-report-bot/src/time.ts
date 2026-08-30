const UNIT_MS: Record<string, number> = {
  s: 1_000,
  m: 60_000,
  h: 3_600_000,
  d: 86_400_000,
};

/**
 * Resolve a Grafana-style relative/absolute time string ("now", "now-7d",
 * an ISO string) to an RFC3339 timestamp the Prometheus HTTP API accepts.
 * Prometheus's query_range endpoint does NOT understand "now-7d" itself —
 * only the Grafana frontend resolves that client-side.
 */
export function resolveTime(input: string, base: Date = new Date()): string {
  if (input === "now") return base.toISOString();

  const match = /^now-(\d+)([smhd])$/.exec(input);
  if (match) {
    const [, amountStr, unit] = match;
    const ms = Number(amountStr) * UNIT_MS[unit];
    return new Date(base.getTime() - ms).toISOString();
  }

  // Assume it's already an absolute timestamp (ISO or Prometheus-parseable).
  return input;
}
