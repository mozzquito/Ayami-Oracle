/**
 * Root-cause investigation hints shown under a breached finding.
 *
 * Data-driven on purpose (per zcode design review, 2026-08-22): keep this as
 * a small table separate from report.ts/config.ts so the hints can be edited
 * without touching the render logic. Matching is (metric, optional group
 * name substring) — first matching rule wins, falling back to the generic
 * per-metric hint if no group-specific rule matches.
 */

export type MetricType = "CPU" | "Memory" | "Storage" | "Down";

interface HintRule {
  metric: MetricType;
  /** case-insensitive substring match against the host group name; omit for a generic/fallback rule */
  groupContains?: string;
  steps: string[];
}

const HINT_RULES: HintRule[] = [
  {
    metric: "CPU",
    groupContains: "mssql",
    steps: [
      "Query sys.dm_exec_requests / sys.dm_exec_query_stats บน SQL Server เพื่อหา query หรือ session ที่กิน CPU สูงสุดช่วงเวลานั้น",
      "ตรวจ Task Scheduler / backup job ที่อาจรันชนช่วง peak",
      "Windows Event Viewer (Application + System log) ช่วงเวลาที่เกิด peak",
    ],
  },
  {
    metric: "CPU",
    steps: [
      "ตรวจ Task Scheduler และ backup job ที่อาจรันช่วงเวลา peak",
      "Windows Event Viewer (Application + System log) ช่วงเวลาที่เกิด peak",
      "ถ้าเครื่องรัน IIS — ตรวจ worker-process recycle/crash ใน IIS log",
    ],
  },
  {
    metric: "Memory",
    steps: [
      "ตรวจ Task Manager / Resource Monitor per-process บนเครื่องจริงช่วงเวลาที่ peak",
      "Windows Event Viewer System log หา memory-pressure event",
      "ถ้าเครื่องรัน IIS — ตรวจ App Pool recycle history (memory-based recycle อาจเป็นตัวบดบังปัญหาจริง)",
    ],
  },
  {
    metric: "Down",
    steps: [
      "เช็คว่าเป็นการ patch/restart/maintenance ที่ตั้งใจอยู่หรือเปล่า ก่อนตกใจ",
      "RDP เข้าเครื่องโดยตรง (หรือเช็คผ่าน vSphere/hypervisor console ถ้า RDP เข้าไม่ได้)",
      "ถ้าเข้าเครื่องได้ — เช็คว่า windows_exporter service หยุดทำงานหรือไม่ (Services.msc)",
      "Windows Event Viewer System log หา unexpected shutdown/crash event ก่อนเวลาที่ล่ม",
    ],
  },
  {
    metric: "Storage",
    steps: [
      "ตรวจการเติบโตของ log file (IIS log, SQL transaction log) บนไดรฟ์ที่ใกล้เต็ม",
      "รัน Disk Cleanup / ตรวจไฟล์ temp และ backup ที่สะสมค้าง",
      "ตรวจ Windows Update cache (WinSxS/SoftwareDistribution) ถ้าไม่ได้เคลียร์มานาน",
    ],
  },
];

export function rootCauseHints(metric: MetricType, groupName: string): string[] {
  const needle = groupName.toLowerCase();
  const specific = HINT_RULES.find((r) => r.metric === metric && r.groupContains && needle.includes(r.groupContains));
  if (specific) return specific.steps;
  const generic = HINT_RULES.find((r) => r.metric === metric && !r.groupContains);
  return generic?.steps ?? [];
}
