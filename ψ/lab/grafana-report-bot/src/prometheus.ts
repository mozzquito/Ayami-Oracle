import type { APIRequestContext } from "playwright";

interface RangeResult {
  status: string;
  data: {
    resultType: string;
    result: Array<{
      metric: Record<string, string>;
      values: [number, string][];
    }>;
  };
}

export interface PeakReading {
  instance: string;
  value: number;
  timestampMs: number;
}

export interface StorageReading {
  instance: string;
  volume: string;
  value: number; // % remaining — LOW is bad, opposite direction from CPU/Memory
  timestampMs: number;
}

interface InstantResult {
  status: string;
  data: {
    resultType: string;
    result: Array<{
      metric: Record<string, string>;
      value: [number, string];
    }>;
  };
}

async function queryInstant(
  request: APIRequestContext,
  baseUrl: string,
  dsUid: string,
  query: string,
): Promise<InstantResult> {
  const url = `${baseUrl}/api/datasources/proxy/uid/${dsUid}/api/v1/query`;
  const res = await request.get(url, { params: { query } });
  if (!res.ok()) throw new Error(`Prometheus query failed: HTTP ${res.status()} — ${query}`);
  return (await res.json()) as InstantResult;
}

/**
 * Instances currently reporting `up == 0` (scrape target unreachable RIGHT
 * NOW — not a windowed peak like the other metrics). Mirrors the exact query
 * used by the "❌ เครื่องล่มตอนนี้" stat panel on the eApp Frontend Errors
 * dashboard (uid eapp-frontend-errors, panel id 4), confirmed 2026-08-23 —
 * `count(up == 0) or vector(0)`. We query the un-counted vector instead so we
 * get the actual instance labels, and match them against HOST_GROUPS
 * ourselves rather than trusting the panel's own (unscoped, whole-Prometheus)
 * count.
 */
export async function currentlyDownInstances(
  request: APIRequestContext,
  baseUrl: string,
  dsUid: string,
): Promise<string[]> {
  const result = await queryInstant(request, baseUrl, dsUid, "up == 0");
  const instances: string[] = [];
  for (const r of result.data.result) {
    if (r.metric.instance) {
      instances.push(r.metric.instance);
    } else {
      console.warn(`up==0 result missing an "instance" label — excluded from down-host check: ${JSON.stringify(r.metric)}`);
    }
  }
  return instances;
}

async function queryRange(
  request: APIRequestContext,
  baseUrl: string,
  dsUid: string,
  query: string,
  start: string,
  end: string,
  stepSeconds = 300,
): Promise<RangeResult> {
  const url = `${baseUrl}/api/datasources/proxy/uid/${dsUid}/api/v1/query_range`;
  const res = await request.get(url, {
    params: { query, start, end, step: `${stepSeconds}s` },
  });
  if (!res.ok()) throw new Error(`Prometheus query_range failed: HTTP ${res.status()} — ${query}`);
  return (await res.json()) as RangeResult;
}

/** Peak CPU% per host, matching the formula validated in the 2026-08-21 investigation. */
export async function peakCpuByInstance(
  request: APIRequestContext,
  baseUrl: string,
  dsUid: string,
  instances: string[],
  start: string,
  end: string,
): Promise<PeakReading[]> {
  const instancePattern = instances.join("|");
  const query = `100 - (avg by (instance) (irate(windows_cpu_time_total{instance=~"${instancePattern}",mode="idle"}[2m])) * 100)`;
  const result = await queryRange(request, baseUrl, dsUid, query, start, end);
  return peaksFromMatrix(result);
}

/** Peak Memory% per host, matching the formula validated in the 2026-08-21 investigation. */
export async function peakMemoryByInstance(
  request: APIRequestContext,
  baseUrl: string,
  dsUid: string,
  instances: string[],
  start: string,
  end: string,
): Promise<PeakReading[]> {
  const instancePattern = instances.join("|");
  const query =
    `100.0 - 100 * windows_os_physical_memory_free_bytes{instance=~"${instancePattern}"}` +
    ` / windows_cs_physical_memory_bytes{instance=~"${instancePattern}"}`;
  const result = await queryRange(request, baseUrl, dsUid, query, start, end);
  return peaksFromMatrix(result);
}

/**
 * Peak combined sent+received network throughput (bits/sec) per host, using
 * the same query shape as the "Network details" panel on Server Monitoring.
 * No agreed threshold exists for this yet — informational only, not risk-flagged.
 */
export async function peakNetworkByInstance(
  request: APIRequestContext,
  baseUrl: string,
  dsUid: string,
  instances: string[],
  start: string,
  end: string,
): Promise<PeakReading[]> {
  const instancePattern = instances.join("|");
  const query =
    `max by (instance) (irate(windows_net_bytes_sent_total{instance=~"${instancePattern}",nic!~"isatap.*|VPN.*"}[2m]))*8` +
    ` + max by (instance) (irate(windows_net_bytes_received_total{instance=~"${instancePattern}",nic!~"isatap.*|VPN.*"}[2m]))*8`;
  const result = await queryRange(request, baseUrl, dsUid, query, start, end);
  return peaksFromMatrix(result);
}

/**
 * Peak combined read+write disk throughput (bytes/sec) per host, using the
 * same query shape as the "Maximum disk read/write" panel on Server Monitoring.
 * No agreed threshold exists for this yet — informational only, not risk-flagged.
 */
export async function peakDiskIoByInstance(
  request: APIRequestContext,
  baseUrl: string,
  dsUid: string,
  instances: string[],
  start: string,
  end: string,
): Promise<PeakReading[]> {
  const instancePattern = instances.join("|");
  const query =
    `max by (instance) (irate(windows_logical_disk_read_bytes_total{instance=~"${instancePattern}"}[2m]))` +
    ` + max by (instance) (irate(windows_logical_disk_write_bytes_total{instance=~"${instancePattern}"}[2m]))`;
  const result = await queryRange(request, baseUrl, dsUid, query, start, end);
  return peaksFromMatrix(result);
}

/**
 * Worst (minimum) % remaining per host+volume — validated against the known
 * critical host (10.0.163.209, volume C:) during the 2026-08-21 investigation.
 */
export async function worstStorageByInstance(
  request: APIRequestContext,
  baseUrl: string,
  dsUid: string,
  instances: string[],
  start: string,
  end: string,
): Promise<StorageReading[]> {
  const instancePattern = instances.join("|");
  const query =
    `100 * windows_logical_disk_free_bytes{instance=~"${instancePattern}"}` +
    ` / windows_logical_disk_size_bytes{instance=~"${instancePattern}"}`;
  const result = await queryRange(request, baseUrl, dsUid, query, start, end);

  const out: StorageReading[] = [];
  for (const series of result.data.result) {
    const instance = series.metric.instance ?? "unknown";
    const volume = series.metric.volume ?? "?";
    let worst: StorageReading | null = null;
    for (const [ts, valStr] of series.values) {
      const value = Number(valStr);
      if (Number.isNaN(value)) continue;
      if (!worst || value < worst.value) {
        worst = { instance, volume, value, timestampMs: ts * 1000 };
      }
    }
    if (worst) out.push(worst);
  }
  return out.sort((a, b) => a.value - b.value);
}

function peaksFromMatrix(result: RangeResult): PeakReading[] {
  const out: PeakReading[] = [];
  for (const series of result.data.result) {
    const instance = series.metric.instance ?? "unknown";
    let best: PeakReading | null = null;
    for (const [ts, valStr] of series.values) {
      const value = Number(valStr);
      if (Number.isNaN(value)) continue;
      if (!best || value > best.value) {
        best = { instance, value, timestampMs: ts * 1000 };
      }
    }
    if (best) out.push(best);
  }
  return out.sort((a, b) => b.value - a.value);
}
