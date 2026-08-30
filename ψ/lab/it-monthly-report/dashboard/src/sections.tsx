import React from "react";
import type { ReportData } from "./types";
import { Card, Field, NumberField, TextArea, Select, StatusPill, Button } from "./ui";
import { getPath, setPath, type Path } from "./setPath";

type SetFn = (path: Path, value: unknown) => void;

function arrayHelpers<T>(data: ReportData, set: SetFn, path: Path) {
  const arr = (getPath(data, path) as T[]) ?? [];
  return {
    items: arr,
    add: (template: T) => set(path, [...arr, template]),
    remove: (idx: number) => set(path, arr.filter((_, i) => i !== idx)),
    update: (idx: number, field: keyof T, value: unknown) => set([...path, idx, field as string], value),
  };
}

// ---------------------------------------------------------------- Meta ----
export function MetaSection({ data, set }: { data: ReportData; set: SetFn }) {
  return (
    <>
      <Card title="ข้อมูลรายงาน">
        <div className="grid-3">
          <Field label="ชื่อลูกค้า" value={data.report.client_name} onChange={(v) => set(["report", "client_name"], v)} />
          <Field label="เดือน" value={data.report.month} onChange={(v) => set(["report", "month"], v)} />
          <NumberField label="ปี" value={data.report.year} onChange={(v) => set(["report", "year"], v)} />
          <Field type="date" label="Report Date" value={data.report.report_date} onChange={(v) => set(["report", "report_date"], v)} />
          <Field type="date" label="Onsite MA" value={data.report.onsite_ma_date} onChange={(v) => set(["report", "onsite_ma_date"], v)} />
          <Field type="date" label="Server/Network Monitor" value={data.report.monitor_date} onChange={(v) => set(["report", "monitor_date"], v)} />
        </div>
      </Card>
      <Card title="Prepared by / Checked by">
        <div className="grid-2">
          <div>
            <h4>Prepared by</h4>
            <Field label="ชื่อ" value={data.prepared_by.name} onChange={(v) => set(["prepared_by", "name"], v)} />
            <Field label="ตำแหน่ง" value={data.prepared_by.role} onChange={(v) => set(["prepared_by", "role"], v)} />
            <Field label="โทร" value={data.prepared_by.phone} onChange={(v) => set(["prepared_by", "phone"], v)} />
            <Field label="อีเมล" value={data.prepared_by.email} onChange={(v) => set(["prepared_by", "email"], v)} />
          </div>
          <div>
            <h4>Checked by</h4>
            <Field label="ชื่อ" value={data.checked_by.name} onChange={(v) => set(["checked_by", "name"], v)} />
            <Field label="ตำแหน่ง" value={data.checked_by.role} onChange={(v) => set(["checked_by", "role"], v)} />
            <Field label="โทร" value={data.checked_by.phone} onChange={(v) => set(["checked_by", "phone"], v)} />
            <Field label="อีเมล" value={data.checked_by.email} onChange={(v) => set(["checked_by", "email"], v)} />
          </div>
        </div>
      </Card>
    </>
  );
}

// ---------------------------------------------------------- Executive ----
export function ExecutiveSection({ data, set }: { data: ReportData; set: SetFn }) {
  const highlights = arrayHelpers<string>(data, set, ["health", "highlights"]);
  const alerts = arrayHelpers<ReportData["health"]["critical_alerts"][number]>(data, set, ["health", "critical_alerts"]);

  return (
    <>
      <Card title="Executive Health Dashboard" right={<StatusPill status={data.health.overall_status} />}>
        <Select
          label="Overall status"
          value={data.health.overall_status}
          options={[
            { value: "green", label: "🟢 Normal" },
            { value: "yellow", label: "🟡 Warning" },
            { value: "red", label: "🔴 Critical" },
          ]}
          onChange={(v) => set(["health", "overall_status"], v)}
        />
        <div className="list-block">
          <span className="field-label">Highlights เดือนนี้</span>
          {highlights.items.map((h, i) => (
            <div className="list-row" key={i}>
              <input value={h ?? ""} onChange={(e) => set(["health", "highlights", i], e.target.value)} />
              <Button variant="ghost" onClick={() => highlights.remove(i)}>ลบ</Button>
            </div>
          ))}
          <Button variant="ghost" onClick={() => highlights.add("")}>+ เพิ่ม highlight</Button>
        </div>
      </Card>

      <Card title="⚠️ Critical Alerts">
        {alerts.items.map((a, i) => (
          <div className="sub-card" key={i}>
            <div className="grid-2">
              <Select
                label="Severity"
                value={a.severity}
                options={[{ value: "red", label: "🔴 Red" }, { value: "yellow", label: "🟡 Yellow" }]}
                onChange={(v) => alerts.update(i, "severity", v)}
              />
              <Field label="หัวข้อ" value={a.title} onChange={(v) => alerts.update(i, "title", v)} />
            </div>
            <TextArea label="รายละเอียด" value={a.description} onChange={(v) => alerts.update(i, "description", v)} />
            <TextArea label="คำแนะนำ" value={a.recommendation} onChange={(v) => alerts.update(i, "recommendation", v)} />
            <Button variant="ghost" onClick={() => alerts.remove(i)}>ลบ alert นี้</Button>
          </div>
        ))}
        <Button variant="ghost" onClick={() => alerts.add({ severity: "red", title: null, description: null, recommendation: null })}>
          + เพิ่ม Critical Alert
        </Button>
      </Card>

      <Card title="SLA Performance">
        <div className="grid-3">
          <NumberField label="Uptime %" value={data.sla.uptime_percent} onChange={(v) => set(["sla", "uptime_percent"], v)} />
          <NumberField label="Avg Response (hrs)" value={data.sla.avg_response_hours} onChange={(v) => set(["sla", "avg_response_hours"], v)} />
          <NumberField label="Avg Resolution (hrs)" value={data.sla.avg_resolution_hours} onChange={(v) => set(["sla", "avg_resolution_hours"], v)} />
          <NumberField label="SLA Met %" value={data.sla.sla_met_percent} onChange={(v) => set(["sla", "sla_met_percent"], v)} />
        </div>
      </Card>

      <Card title="Trend (Month-over-Month)">
        <div className="grid-2">
          <NumberField label="Ticket count — เดือนนี้" value={data.trend_mom.ticket_count.this_month} onChange={(v) => set(["trend_mom", "ticket_count", "this_month"], v)} />
          <NumberField label="Ticket count — เดือนก่อน" value={data.trend_mom.ticket_count.last_month} onChange={(v) => set(["trend_mom", "ticket_count", "last_month"], v)} />
          <NumberField label="Uptime % — เดือนนี้" value={data.trend_mom.uptime_percent.this_month} onChange={(v) => set(["trend_mom", "uptime_percent", "this_month"], v)} />
          <NumberField label="Uptime % — เดือนก่อน" value={data.trend_mom.uptime_percent.last_month} onChange={(v) => set(["trend_mom", "uptime_percent", "last_month"], v)} />
        </div>
      </Card>
    </>
  );
}

// ---------------------------------------------------------- Computers ----
export function ComputersSection({ data, set }: { data: ReportData; set: SetFn }) {
  const c = data.computers;
  const total = c.by_type.desktop + c.by_type.laptop + c.by_type.all_in_one + c.by_type.macbook;
  const aging = c.age_distribution["5_7y"] + c.age_distribution.over_7y;
  const agingPct = total ? Math.round((aging / total) * 100) : 0;

  return (
    <Card title="Computer">
      <div className="grid-2">
        <NumberField label="จำนวนตามสัญญา" value={c.contract_count} onChange={(v) => set(["computers", "contract_count"], v)} />
        <NumberField label="ได้รับบริการเดือนนี้" value={c.serviced_count} onChange={(v) => set(["computers", "serviced_count"], v)} />
      </div>
      <h4>แยกตามประเภท</h4>
      <div className="grid-4">
        <NumberField label="Desktop" value={c.by_type.desktop} onChange={(v) => set(["computers", "by_type", "desktop"], v ?? 0)} />
        <NumberField label="Laptop" value={c.by_type.laptop} onChange={(v) => set(["computers", "by_type", "laptop"], v ?? 0)} />
        <NumberField label="All-in-One" value={c.by_type.all_in_one} onChange={(v) => set(["computers", "by_type", "all_in_one"], v ?? 0)} />
        <NumberField label="MacBook" value={c.by_type.macbook} onChange={(v) => set(["computers", "by_type", "macbook"], v ?? 0)} />
      </div>
      <h4>Hard disk / Battery</h4>
      <div className="grid-4">
        <NumberField label="HDD Normal" value={c.hard_disk.normal} onChange={(v) => set(["computers", "hard_disk", "normal"], v ?? 0)} />
        <NumberField label="HDD Caution" value={c.hard_disk.caution} onChange={(v) => set(["computers", "hard_disk", "caution"], v ?? 0)} />
        <NumberField label="Battery OK" value={c.battery.ok} onChange={(v) => set(["computers", "battery", "ok"], v ?? 0)} />
        <NumberField label="Battery Degraded" value={c.battery.degraded} onChange={(v) => set(["computers", "battery", "degraded"], v ?? 0)} />
      </div>
      <h4>อายุเครื่อง</h4>
      <div className="grid-5">
        <NumberField label="<1 ปี" value={c.age_distribution.under_1y} onChange={(v) => set(["computers", "age_distribution", "under_1y"], v ?? 0)} />
        <NumberField label="1-2 ปี" value={c.age_distribution["1_2y"]} onChange={(v) => set(["computers", "age_distribution", "1_2y"], v ?? 0)} />
        <NumberField label="2-4 ปี" value={c.age_distribution["2_4y"]} onChange={(v) => set(["computers", "age_distribution", "2_4y"], v ?? 0)} />
        <NumberField label="5-7 ปี" value={c.age_distribution["5_7y"]} onChange={(v) => set(["computers", "age_distribution", "5_7y"], v ?? 0)} />
        <NumberField label=">7 ปี" value={c.age_distribution.over_7y} onChange={(v) => set(["computers", "age_distribution", "over_7y"], v ?? 0)} />
      </div>
      {total > 0 && agingPct >= 50 && (
        <p className="alert-inline">🟡 {agingPct}% ของเครื่องอายุเกิน 5 ปี — แนะนำวาง replacement roadmap</p>
      )}
      <TextArea label="Recommendation" value={c.replacement_recommendation} onChange={(v) => set(["computers", "replacement_recommendation"], v)} />
    </Card>
  );
}

// ----------------------------------------------------------- Software ----
export function licenseStatus(expire: string | null): { text: string; className: string } {
  if (!expire) return { text: "-", className: "" };
  const d = new Date(expire);
  if (isNaN(d.getTime())) return { text: "invalid date", className: "pill-missing" };
  const days = Math.round((d.getTime() - Date.now()) / 86_400_000);
  if (days < 0) return { text: `🔴 EXPIRED (${-days}d ago)`, className: "pill-red" };
  if (days <= 30) return { text: `🟡 expires in ${days}d`, className: "pill-yellow" };
  return { text: "🟢 OK", className: "pill-green" };
}

function LicenseTable({
  title,
  data,
  set,
  path,
}: {
  title: string;
  data: ReportData;
  set: SetFn;
  path: Path;
}) {
  const helpers = arrayHelpers<ReportData["software"]["os_licenses"][number]>(data, set, path);
  return (
    <div>
      <h4>{title}</h4>
      <table className="mini-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Amount</th>
            <th>Expire</th>
            <th>Status</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {helpers.items.map((i, idx) => {
            const status = licenseStatus(i.expire);
            return (
              <tr key={idx}>
                <td><input value={i.name ?? ""} onChange={(e) => helpers.update(idx, "name", e.target.value)} /></td>
                <td><input type="number" value={i.amount ?? 0} onChange={(e) => helpers.update(idx, "amount", Number(e.target.value))} style={{ width: 60 }} /></td>
                <td><input type="date" value={i.expire ?? ""} onChange={(e) => helpers.update(idx, "expire", e.target.value)} /></td>
                <td><span className={`pill ${status.className}`}>{status.text}</span></td>
                <td><Button variant="ghost" onClick={() => helpers.remove(idx)}>ลบ</Button></td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <Button variant="ghost" onClick={() => helpers.add({ name: null, amount: 1, expire: null })}>+ เพิ่มรายการ</Button>
    </div>
  );
}

export function SoftwareSection({ data, set }: { data: ReportData; set: SetFn }) {
  const allLicenses = [...data.software.os_licenses, ...data.software.office_licenses];
  const computedAlerts = allLicenses
    .filter((i) => i.name)
    .map((i) => ({ name: i.name, ...licenseStatus(i.expire) }))
    .filter((i) => i.className === "pill-red" || i.className === "pill-yellow");

  return (
    <Card title="Software & License Tracking">
      <LicenseTable title="Operating Systems" data={data} set={set} path={["software", "os_licenses"]} />
      <LicenseTable title="Office / Productivity" data={data} set={set} path={["software", "office_licenses"]} />
      {computedAlerts.length > 0 && (
        <p className="alert-inline">
          ⚠️ License alerts: {computedAlerts.map((a) => `${a.name} (${a.text})`).join(" · ")}
        </p>
      )}
    </Card>
  );
}

// ------------------------------------------------------------- Server ----
export function ServerSection({ data, set }: { data: ReportData; set: SetFn }) {
  const servers = arrayHelpers<ReportData["server"]["physical_servers"][number]>(data, set, ["server", "physical_servers"]);
  return (
    <Card title="Server">
      <div className="grid-2">
        <NumberField label="จำนวนตามสัญญา" value={data.server.contract_count} onChange={(v) => set(["server", "contract_count"], v)} />
        <NumberField label="ได้รับบริการเดือนนี้" value={data.server.serviced_count} onChange={(v) => set(["server", "serviced_count"], v)} />
      </div>
      <h4>Physical Servers</h4>
      {servers.items.map((s, i) => (
        <div className="sub-card" key={i}>
          <div className="grid-3">
            <Field label="Model" value={s.model} onChange={(v) => servers.update(i, "model", v)} />
            <Field label="CPU" value={s.cpu} onChange={(v) => servers.update(i, "cpu", v)} />
            <NumberField label="RAM (GB)" value={s.ram_gb} onChange={(v) => servers.update(i, "ram_gb", v)} />
            <Field label="Disk" value={s.disk} onChange={(v) => servers.update(i, "disk", v)} />
            <Field label="OS" value={s.os} onChange={(v) => servers.update(i, "os", v)} />
            <Field label="Role" value={s.role} onChange={(v) => servers.update(i, "role", v)} />
          </div>
          <Select
            label="Status"
            value={s.status as any}
            options={[{ value: "normal", label: "🟢 Normal" }, { value: "warning", label: "🟡 Warning" }, { value: "critical", label: "🔴 Critical" }]}
            onChange={(v) => servers.update(i, "status", v)}
          />
          <Button variant="ghost" onClick={() => servers.remove(i)}>ลบ server นี้</Button>
        </div>
      ))}
      <Button variant="ghost" onClick={() => servers.add({ model: null, cpu: null, ram_gb: null, disk: null, os: null, role: null, status: null })}>
        + เพิ่ม server
      </Button>

      <h4>Backup</h4>
      <div className="grid-2">
        <Select
          label="Scheduled backup status"
          value={data.server.backup.scheduled_status as any}
          options={[{ value: "ok", label: "🟢 OK" }, { value: "issue", label: "🔴 Issue" }]}
          onChange={(v) => set(["server", "backup", "scheduled_status"], v)}
        />
        <Field type="date" label="Last restore test verified" value={data.server.backup.last_restore_test} onChange={(v) => set(["server", "backup", "last_restore_test"], v)} />
      </div>
      {!data.server.backup.last_restore_test && (
        <p className="alert-inline">⚠️ ยังไม่เคยทดสอบ restore จริง — แนะนำทดสอบอย่างน้อยไตรมาสละครั้ง</p>
      )}
    </Card>
  );
}

// ------------------------------------------------------- Firewall/Net ----
function DeviceTable({
  title,
  data,
  set,
  path,
  showType,
  showFirmware,
}: {
  title: string;
  data: ReportData;
  set: SetFn;
  path: Path;
  showType?: boolean;
  showFirmware?: boolean;
}) {
  const helpers = arrayHelpers<ReportData["network"]["devices"][number]>(data, set, path);
  return (
    <div>
      <h4>{title}</h4>
      {helpers.items.map((d, i) => (
        <div className="sub-card" key={i}>
          <div className="grid-3">
            <Field label={showType ? "Type" : "Name"} value={(showType ? d.type : d.name) ?? null} onChange={(v) => helpers.update(i, (showType ? "type" : "name") as any, v)} />
            {showType && <NumberField label="Count" value={d.count ?? 0} onChange={(v) => helpers.update(i, "count", v ?? 0)} />}
            <Select
              label="Status"
              value={d.status as any}
              options={[{ value: "normal", label: "🟢 Normal" }, { value: "warning", label: "🟡 Warning" }, { value: "critical", label: "🔴 Critical" }]}
              onChange={(v) => helpers.update(i, "status", v)}
            />
            {showFirmware && <Field label="Firmware" value={d.firmware ?? null} onChange={(v) => helpers.update(i, "firmware", v)} />}
            {showFirmware && <Field type="date" label="License Expiry" value={d.license_expiry ?? null} onChange={(v) => helpers.update(i, "license_expiry", v)} />}
          </div>
          <Button variant="ghost" onClick={() => helpers.remove(i)}>ลบ</Button>
        </div>
      ))}
      <Button
        variant="ghost"
        onClick={() =>
          helpers.add(
            showType
              ? ({ type: null, count: 1, status: null } as any)
              : ({ name: null, status: null, firmware: null, license_expiry: null } as any),
          )
        }
      >
        + เพิ่มอุปกรณ์
      </Button>
    </div>
  );
}

export function InfraSection({ data, set }: { data: ReportData; set: SetFn }) {
  const noFirewallStatus = data.firewall_gateway.devices.length === 0 || data.firewall_gateway.devices.every((d) => !d.status);
  return (
    <>
      <Card title="Firewall / Gateway">
        <DeviceTable title="Devices" data={data} set={set} path={["firewall_gateway", "devices"]} showFirmware />
        <Field label="Warning/Critical log" value={data.firewall_gateway.warning_critical_log} onChange={(v) => set(["firewall_gateway", "warning_critical_log"], v)} />
        {noFirewallStatus && (
          <p className="alert-inline">🔴 ไม่มีข้อมูลสถานะ firewall เลย — ควรกรอกให้ครบ ไม่เช่นนั้นลูกค้าจะตั้งคำถามว่ามีการดูแลจริงหรือไม่</p>
        )}
      </Card>
      <Card title="Network">
        <DeviceTable title="Devices" data={data} set={set} path={["network", "devices"]} showType />
        <Field label="Warning/Critical log" value={data.network.warning_critical_log} onChange={(v) => set(["network", "warning_critical_log"], v)} />
      </Card>
    </>
  );
}

// ------------------------------------------------------------ Tickets ----
/** Minimal CSV parser: header row + rows, handles quoted fields with commas.
 *  Deliberately not RFC-4180-complete — the input is a controlled export. */
function parseCsv(text: string): Record<string, string>[] {
  const parseLine = (line: string): string[] => {
    const fields: string[] = [];
    let cur = "";
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (inQuotes) {
        if (ch === '"' && line[i + 1] === '"') { cur += '"'; i++; }
        else if (ch === '"') inQuotes = false;
        else cur += ch;
      } else if (ch === '"') inQuotes = true;
      else if (ch === ",") { fields.push(cur); cur = ""; }
      else cur += ch;
    }
    fields.push(cur);
    return fields.map((f) => f.trim());
  };
  const lines = text.split(/\r?\n/).filter((l) => l.trim().length > 0);
  if (lines.length < 2) return [];
  const headers = parseLine(lines[0]).map((h) => h.toLowerCase());
  return lines.slice(1).map((line) => {
    const values = parseLine(line);
    const row: Record<string, string> = {};
    headers.forEach((h, i) => (row[h] = values[i] ?? ""));
    return row;
  });
}

const TICKET_CSV_COLUMNS = ["name", "detail", "status", "responsible", "start", "end", "resolution"] as const;

export function TicketsSection({
  data,
  set,
  onError,
}: {
  data: ReportData;
  set: SetFn;
  onError?: (msg: string) => void;
}) {
  const tickets = arrayHelpers<ReportData["tickets"]["list"][number]>(data, set, ["tickets", "list"]);

  function handleCsvFile(file: File) {
    file
      .text()
      .then((text) => {
        const rows = parseCsv(text);
        if (rows.length === 0) {
          onError?.("CSV ว่างเปล่าหรืออ่านไม่ได้ — ต้องมี header row + อย่างน้อย 1 แถวข้อมูล");
          return;
        }
        const missingCols = TICKET_CSV_COLUMNS.filter((c) => !(c in rows[0]));
        if (missingCols.length > 0) {
          onError?.(`CSV ขาด column: ${missingCols.join(", ")} — ต้องมี name,detail,status,responsible,start,end,resolution`);
          return;
        }
        const newTickets = rows.map((r) => ({
          name: r.name ?? "",
          detail: r.detail ?? "",
          status: r.status ?? "",
          responsible: r.responsible ?? "",
          start: r.start ?? "",
          end: r.end ?? "",
          resolution: r.resolution ?? "",
        }));
        set(["tickets", "list"], [...tickets.items, ...newTickets]);
      })
      .catch((e) => onError?.(`อ่านไฟล์ CSV ไม่สำเร็จ: ${e}`));
  }

  return (
    <Card title="Ticket Report (เดือนนี้เท่านั้น)">
      <div className="grid-4">
        <NumberField label="Incident" value={data.tickets.incident_count} onChange={(v) => set(["tickets", "incident_count"], v ?? 0)} />
        <NumberField label="Service Request" value={data.tickets.service_request_count} onChange={(v) => set(["tickets", "service_request_count"], v ?? 0)} />
        <NumberField label="In progress" value={data.tickets.status.in_progress} onChange={(v) => set(["tickets", "status", "in_progress"], v ?? 0)} />
        <NumberField label="Done" value={data.tickets.status.done} onChange={(v) => set(["tickets", "status", "done"], v ?? 0)} />
      </div>
      <h4>รายการ ticket</h4>
      <div className="list-row">
        <label className="btn btn-ghost" style={{ cursor: "pointer" }}>
          📥 Import CSV (name,detail,status,responsible,start,end,resolution)
          <input
            type="file"
            accept=".csv"
            style={{ display: "none" }}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleCsvFile(file);
              e.target.value = "";
            }}
          />
        </label>
      </div>
      {tickets.items.map((t, i) => (
        <div className="sub-card" key={i}>
          <div className="grid-3">
            <Field label="ชื่อ" value={t.name} onChange={(v) => tickets.update(i, "name", v)} />
            <Field label="สถานะ" value={t.status} onChange={(v) => tickets.update(i, "status", v)} />
            <Field label="ผู้รับผิดชอบ" value={t.responsible} onChange={(v) => tickets.update(i, "responsible", v)} />
            <Field type="date" label="เริ่ม" value={t.start} onChange={(v) => tickets.update(i, "start", v)} />
            <Field type="date" label="จบ" value={t.end} onChange={(v) => tickets.update(i, "end", v)} />
          </div>
          <TextArea label="รายละเอียด" value={t.detail} onChange={(v) => tickets.update(i, "detail", v)} />
          <TextArea label="วิธีแก้ไข" value={t.resolution} onChange={(v) => tickets.update(i, "resolution", v)} />
          <Button variant="ghost" onClick={() => tickets.remove(i)}>ลบ ticket นี้</Button>
        </div>
      ))}
      <Button variant="ghost" onClick={() => tickets.add({ name: "", detail: "", status: "Open", responsible: "", start: "", end: "", resolution: "" })}>
        + เพิ่ม ticket
      </Button>
    </Card>
  );
}

// -------------------------------------------------------- Scope/Recs ----
export function ScopeSection({ data, set }: { data: ReportData; set: SetFn }) {
  const scope = arrayHelpers<ReportData["scope_of_work"][number]>(data, set, ["scope_of_work"]);
  return (
    <Card title="Scope of Work Check">
      {scope.items.map((s, i) => (
        <div className="list-row" key={i}>
          <input style={{ flex: 1 }} value={s.item ?? ""} onChange={(e) => scope.update(i, "item", e.target.value)} />
          <label className="checkbox">
            <input type="checkbox" checked={!!s.delivered} onChange={(e) => scope.update(i, "delivered", e.target.checked)} />
            Delivered
          </label>
          <Button variant="ghost" onClick={() => scope.remove(i)}>ลบ</Button>
        </div>
      ))}
      <Button variant="ghost" onClick={() => scope.add({ item: null, delivered: false })}>+ เพิ่มรายการ</Button>
    </Card>
  );
}

export function RecommendationsSection({ data, set }: { data: ReportData; set: SetFn }) {
  const recs = arrayHelpers<ReportData["recommendations"][number]>(data, set, ["recommendations"]);
  return (
    <>
      <Card title="Recommendations">
        {recs.items.map((r, i) => (
          <div className="list-row" key={i}>
            <select value={r.priority} onChange={(e) => recs.update(i, "priority", e.target.value)} style={{ width: 110 }}>
              <option value="high">HIGH</option>
              <option value="medium">MEDIUM</option>
              <option value="low">LOW</option>
            </select>
            <input style={{ flex: 1 }} value={r.text ?? ""} onChange={(e) => recs.update(i, "text", e.target.value)} />
            <Button variant="ghost" onClick={() => recs.remove(i)}>ลบ</Button>
          </div>
        ))}
        <Button variant="ghost" onClick={() => recs.add({ priority: "medium", text: null })}>+ เพิ่มคำแนะนำ</Button>
      </Card>
      <Card title="Sign-off">
        <div className="grid-2">
          <Field label="ชื่อผู้เซ็นรับทราบ (ลูกค้า)" value={data.sign_off.client_signer_name} onChange={(v) => set(["sign_off", "client_signer_name"], v)} />
          <Field type="date" label="วันที่เซ็น" value={data.sign_off.client_signed_date} onChange={(v) => set(["sign_off", "client_signed_date"], v)} />
        </div>
      </Card>
    </>
  );
}
