import type { ReportData } from "./types";
import { licenseStatus } from "./sections";

export interface PreflightItem {
  ok: boolean;
  label: string;
}

/** Non-blocking readiness checklist shown before Generate Report. */
export function computePreflight(data: ReportData): PreflightItem[] {
  const items: PreflightItem[] = [
    { ok: !!data.report.client_name, label: "ชื่อลูกค้า (report.client_name)" },
    { ok: !!data.report.report_date, label: "วันที่ออกรายงาน (report.report_date)" },
    { ok: !!data.health.overall_status, label: "สถานะรวม (health.overall_status)" },
    { ok: data.sla.uptime_percent !== null, label: "SLA uptime %" },
  ];

  const allLicenses = [...data.software.os_licenses, ...data.software.office_licenses];
  const licenseAlertCount = allLicenses
    .filter((i) => i.name)
    .map((i) => licenseStatus(i.expire))
    .filter((s) => s.className === "pill-red" || s.className === "pill-yellow").length;
  if (licenseAlertCount > 0) {
    items.push({
      ok: data.recommendations.length > 0,
      label: `License ใกล้หมด/หมดอายุ ${licenseAlertCount} รายการ — มี recommendation รองรับหรือยัง`,
    });
  }

  const namedAlerts = data.health.critical_alerts.filter((a) => a.title);
  if (namedAlerts.length > 0) {
    const missingRec = namedAlerts.filter((a) => !a.recommendation).length;
    items.push({
      ok: missingRec === 0,
      label: missingRec > 0 ? `Critical alert ${missingRec} รายการยังไม่มีคำแนะนำ` : "Critical alerts มีคำแนะนำครบ",
    });
  }

  return items;
}
