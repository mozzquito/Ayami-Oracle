export interface DashboardTarget {
  key: string;
  uid: string;
  title: string;
  /** if true, also pull Prometheus peak values per host group for CPU/Memory panels */
  extractPeaks: boolean;
}

// Known dashboards on this Grafana instance, found via /api/search on 2026-08-21.
// Re-run `bun run src/cli.ts list` if these UIDs ever change.
export const DASHBOARDS: DashboardTarget[] = [
  { key: "server", uid: "Kdh0OoSGz", title: "Server Monitoring", extractPeaks: true },
  { key: "iis", uid: "__gEPv6Mzjhh", title: "IIS Monitoring", extractPeaks: false },
  { key: "mssql", uid: "xButrvtZk", title: "MSSQL Monitor", extractPeaks: false },
];

export interface HostGroup {
  name: string;
  /** windows_exporter instance labels, e.g. "10.0.165.11:9182" */
  instances: string[];
}

// Manually curated from the dashboard's $job/$app template variables + the
// Storage table in the weekly report, as of 2026-08-21. Update if the fleet changes.
export const HOST_GROUPS: HostGroup[] = [
  {
    name: "Backoffice",
    instances: [
      "10.0.165.11:9182",
      "10.0.165.12:9182",
      "10.0.165.13:9182",
      "10.0.165.14:9182",
    ],
  },
  {
    name: "E-VISA",
    instances: [
      "10.0.163.202:9182",
      "10.0.163.203:9182",
      "10.0.163.204:9182",
      "10.0.163.206:9182",
      "10.0.163.207:9182",
      "10.0.163.208:9182",
      "10.0.163.209:9182",
      "10.0.163.61:9182",
    ],
  },
  {
    name: "MSSQL",
    instances: ["10.0.163.8:9182", "10.0.163.11:9182"],
  },
];

// Thresholds agreed for the weekly report (see ψ/memory/retrospectives/2026-08/22).
export const CPU_THRESHOLD_PCT = 80;
export const MEMORY_THRESHOLD_PCT = 80;
export const STORAGE_REMAINING_THRESHOLD_PCT = 10;
