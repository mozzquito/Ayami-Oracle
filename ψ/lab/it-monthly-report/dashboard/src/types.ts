// Mirrors ψ/lab/it-monthly-report/schema.yaml — keep in sync by hand.
export type Status = "green" | "yellow" | "red" | null;

export interface ClientProfile {
  client_name: string;
  contact_name: string | null;
  contact_email: string | null;
  contract_ref: string | null;
}
export type Priority = "high" | "medium" | "low";

export interface Person {
  name: string | null;
  role: string | null;
  phone: string | null;
  email: string | null;
}

export interface CriticalAlert {
  severity: "red" | "yellow";
  title: string | null;
  description: string | null;
  recommendation: string | null;
}

export interface LicenseItem {
  name: string | null;
  amount: number;
  expire: string | null;
}

export interface PhysicalServer {
  model: string | null;
  cpu: string | null;
  ram_gb: number | null;
  disk: string | null;
  os: string | null;
  role: string | null;
  status: string | null;
}

export interface GuestVM {
  name: string;
  vcpu: string;
  vram: string;
  disk: string;
  os: string;
}

export interface Device {
  name?: string | null;
  type?: string | null;
  count?: number;
  status: string | null;
  firmware?: string | null;
  license_expiry?: string | null;
}

export interface Ticket {
  name: string;
  detail: string;
  status: string;
  responsible: string;
  start: string;
  end: string;
  resolution: string;
}

export interface ScopeItem {
  item: string | null;
  delivered: boolean | null;
}

export interface Recommendation {
  priority: Priority;
  text: string | null;
}

export interface ReportData {
  report: {
    title: string;
    month: string;
    year: number;
    client_name: string | null;
    report_date: string | null;
    onsite_ma_date: string | null;
    monitor_date: string | null;
  };
  prepared_by: Person;
  checked_by: Person;
  health: {
    overall_status: Status;
    highlights: (string | null)[];
    critical_alerts: CriticalAlert[];
  };
  sla: {
    uptime_percent: number | null;
    avg_response_hours: number | null;
    avg_resolution_hours: number | null;
    sla_met_percent: number | null;
  };
  trend_mom: {
    ticket_count: { this_month: number | null; last_month: number | null };
    uptime_percent: { this_month: number | null; last_month: number | null };
    recurring_issues: string[];
  };
  computers: {
    contract_count: number | null;
    serviced_count: number | null;
    by_type: { desktop: number; laptop: number; all_in_one: number; macbook: number };
    hard_disk: { normal: number; caution: number };
    battery: { ok: number; degraded: number };
    age_distribution: {
      under_1y: number;
      "1_2y": number;
      "2_4y": number;
      "5_7y": number;
      over_7y: number;
    };
    replacement_recommendation: string | null;
  };
  software: {
    os_licenses: LicenseItem[];
    office_licenses: LicenseItem[];
    license_alerts: string[];
  };
  server: {
    contract_count: number | null;
    serviced_count: number | null;
    physical_servers: PhysicalServer[];
    guest_vms: GuestVM[];
    backup: { scheduled_status: string | null; last_restore_test: string | null };
  };
  firewall_gateway: {
    devices: Device[];
    warning_critical_log: string | null;
  };
  network: {
    devices: Device[];
    warning_critical_log: string | null;
  };
  tickets: {
    incident_count: number;
    service_request_count: number;
    status: { in_progress: number; pending: number; done: number };
    list: Ticket[];
  };
  scope_of_work: ScopeItem[];
  recommendations: Recommendation[];
  sign_off: { client_signer_name: string | null; client_signed_date: string | null };
}

export function emptyReportData(month: string, year: number): ReportData {
  return {
    report: {
      title: "IT Service Monthly Report",
      month,
      year,
      client_name: null,
      report_date: null,
      onsite_ma_date: null,
      monitor_date: null,
    },
    prepared_by: { name: null, role: "IT Specialist", phone: null, email: null },
    checked_by: { name: null, role: "Project Manager", phone: null, email: null },
    health: { overall_status: null, highlights: [], critical_alerts: [] },
    sla: {
      uptime_percent: null,
      avg_response_hours: null,
      avg_resolution_hours: null,
      sla_met_percent: null,
    },
    trend_mom: {
      ticket_count: { this_month: null, last_month: null },
      uptime_percent: { this_month: null, last_month: null },
      recurring_issues: [],
    },
    computers: {
      contract_count: null,
      serviced_count: null,
      by_type: { desktop: 0, laptop: 0, all_in_one: 0, macbook: 0 },
      hard_disk: { normal: 0, caution: 0 },
      battery: { ok: 0, degraded: 0 },
      age_distribution: { under_1y: 0, "1_2y": 0, "2_4y": 0, "5_7y": 0, over_7y: 0 },
      replacement_recommendation: null,
    },
    software: { os_licenses: [], office_licenses: [], license_alerts: [] },
    server: {
      contract_count: null,
      serviced_count: null,
      physical_servers: [],
      guest_vms: [],
      backup: { scheduled_status: null, last_restore_test: null },
    },
    firewall_gateway: { devices: [], warning_critical_log: null },
    network: { devices: [], warning_critical_log: null },
    tickets: {
      incident_count: 0,
      service_request_count: 0,
      status: { in_progress: 0, pending: 0, done: 0 },
      list: [],
    },
    scope_of_work: [],
    recommendations: [],
    sign_off: { client_signer_name: null, client_signed_date: null },
  };
}
