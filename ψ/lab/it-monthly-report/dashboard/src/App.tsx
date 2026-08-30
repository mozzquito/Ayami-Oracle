import React, { useEffect, useState } from "react";
import yaml from "js-yaml";
import { api } from "./api";
import type { ReportData, ClientProfile } from "./types";
import { setPath, type Path } from "./setPath";
import { deepMerge, extractYaml } from "./merge";
import { computePreflight } from "./preflight";
import { Button, StatusPill } from "./ui";
import {
  MetaSection,
  ExecutiveSection,
  ComputersSection,
  SoftwareSection,
  ServerSection,
  InfraSection,
  TicketsSection,
  ScopeSection,
  RecommendationsSection,
} from "./sections";

const SECTIONS = [
  { id: "meta", label: "ข้อมูลรายงาน" },
  { id: "exec", label: "Executive & SLA" },
  { id: "computers", label: "Computer" },
  { id: "software", label: "Software & License" },
  { id: "server", label: "Server" },
  { id: "infra", label: "Firewall / Network" },
  { id: "tickets", label: "Ticket Report" },
  { id: "scope", label: "Scope of Work" },
  { id: "recs", label: "Recommendations" },
] as const;
type SectionId = (typeof SECTIONS)[number]["id"];

function computeAlertCount(data: ReportData): number {
  let n = data.health.critical_alerts.filter((a) => a.title).length;
  if (data.server.backup.scheduled_status && !data.server.backup.last_restore_test) n += 1;
  return n;
}

export default function App() {
  const [clients, setClients] = useState<string[]>([]);
  const [currentClient, setCurrentClient] = useState<string | null>(null);
  const [months, setMonths] = useState<string[]>([]);
  const [currentFile, setCurrentFile] = useState<string | null>(null);
  const [data, setData] = useState<ReportData | null>(null);
  const [dirty, setDirty] = useState(false);
  const [section, setSection] = useState<SectionId>("meta");
  const [busy, setBusy] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const [newKey, setNewKey] = useState("");
  const [newMonthName, setNewMonthName] = useState("");
  const [showNewForm, setShowNewForm] = useState(false);

  const [newClientCode, setNewClientCode] = useState("");
  const [newClientName, setNewClientName] = useState("");
  const [showNewClientForm, setShowNewClientForm] = useState(false);

  const [changelog, setChangelog] = useState<string[]>([]);
  const [changelogPrevMonth, setChangelogPrevMonth] = useState<string | null>(null);

  // AI assist panel
  const [aiTool, setAiTool] = useState<"zcode" | "agy">("agy");
  const [aiNotes, setAiNotes] = useState("");
  const [aiOutput, setAiOutput] = useState<string | null>(null);
  const [aiParsed, setAiParsed] = useState<unknown | null>(null);
  const [aiOpen, setAiOpen] = useState(false);
  const [preflightOpen, setPreflightOpen] = useState(false);

  useEffect(() => {
    api.listClients().then((r) => setClients(r.clients)).catch((e) => setToast(String(e)));
  }, []);

  useEffect(() => {
    if (clients.length && !currentClient) setCurrentClient(clients[0]);
  }, [clients, currentClient]);

  useEffect(() => {
    if (!currentClient) return;
    setCurrentFile(null);
    setData(null);
    api
      .listMonths(currentClient)
      .then((r) => setMonths(r.files))
      .catch((e) => setToast(String(e)));
  }, [currentClient]);

  async function loadFile(file: string) {
    if (!currentClient) return;
    setBusy("loading");
    try {
      const r = await api.loadData(currentClient, file);
      setData(r.data);
      setCurrentFile(file);
      setDirty(false);
      setChangelog([]);
      setChangelogPrevMonth(null);
      api
        .changelog(currentClient, file)
        .then((cl) => {
          setChangelog(cl.changelog);
          setChangelogPrevMonth(cl.prevMonth);
        })
        .catch(() => {});
    } catch (e) {
      setToast(String(e));
    } finally {
      setBusy(null);
    }
  }

  useEffect(() => {
    if (months.length && !currentFile) loadFile(months[0]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [months]);

  function set(path: Path, value: unknown) {
    setData((d) => (d ? setPath(d, path, value) : d));
    setDirty(true);
  }

  async function handleSave() {
    if (!data || !currentFile || !currentClient) return;
    setBusy("saving");
    try {
      await api.saveData(currentClient, currentFile, data);
      setDirty(false);
      setToast(`บันทึกแล้ว: ${currentClient}/${currentFile}`);
    } catch (e) {
      setToast(String(e));
    } finally {
      setBusy(null);
    }
  }

  async function handleGenerate() {
    if (!data || !currentFile || !currentClient) return;
    setBusy("generating");
    try {
      if (dirty) await api.saveData(currentClient, currentFile, data);
      const r = await api.generate(currentClient, currentFile);
      setDirty(false);
      setToast(`สร้างรายงานแล้ว: ${r.md} + ${r.docx}`);
    } catch (e) {
      setToast(String(e));
    } finally {
      setBusy(null);
    }
  }

  async function handleCreateMonth() {
    if (!newKey.trim() || !currentClient) return;
    const key = newKey.trim();
    const file = `${key}.yaml`;
    const year = parseInt(key.slice(0, 4), 10) || new Date().getFullYear();
    const MONTHS = ["January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"];
    const mm = Number(key.slice(5, 7));
    const monthName = newMonthName.trim() ||
      (Number.isInteger(mm) && mm >= 1 && mm <= 12 ? MONTHS[mm - 1] : "");
    if (!monthName) {
      setToast("File key ต้องเป็น YYYY-MM เช่น 2026-08 (หรือพิมพ์ชื่อเดือนเอง)");
      return;
    }
    setBusy("creating");
    try {
      const r = await api.newMonth(currentClient, file, monthName, year);
      const list = await api.listMonths(currentClient);
      setMonths(list.files);
      await loadFile(file);
      setShowNewForm(false);
      setNewKey("");
      setNewMonthName("");
      setToast(
        r.carried
          ? `สร้างเดือนใหม่แล้ว — นำข้อมูล asset จากเดือน ${r.prevMonth} มาเป็น baseline แล้ว ตรวจสอบก่อนบันทึก`
          : "สร้างเดือนใหม่แล้ว (เดือนแรกของลูกค้านี้ ไม่มี baseline ให้ carry-forward)",
      );
    } catch (e) {
      setToast(String(e));
    } finally {
      setBusy(null);
    }
  }

  async function handleCreateClient() {
    if (!newClientCode.trim() || !newClientName.trim()) return;
    const code = newClientCode.trim().toLowerCase().replace(/[^a-z0-9_-]/g, "");
    setBusy("creating-client");
    try {
      const profile: ClientProfile = {
        client_name: newClientName.trim(),
        contact_name: null,
        contact_email: null,
        contract_ref: null,
      };
      await api.saveProfile(code, profile);
      const r = await api.listClients();
      setClients(r.clients);
      setCurrentClient(code);
      setShowNewClientForm(false);
      setNewClientCode("");
      setNewClientName("");
      setToast(`สร้างลูกค้าใหม่แล้ว: ${newClientName} — ต่อไปสร้างเดือนแรกได้เลย`);
    } catch (e) {
      setToast(String(e));
    } finally {
      setBusy(null);
    }
  }

  async function handleAiAssist() {
    if (!aiNotes.trim()) return;
    setBusy("ai");
    setAiOutput(null);
    setAiParsed(null);
    try {
      const { schema } = await api.schema();
      const currentYaml = data ? yaml.dump(data, { lineWidth: 100 }) : "";
      const prompt = [
        "คุณกำลังช่วยกรอกข้อมูลรายงาน IT Service Monthly Report ตาม schema YAML ด้านล่าง",
        "อ่านรายละเอียดที่ผู้ใช้เล่ามา แล้วแปลงเป็น YAML ที่ตรงกับ schema นี้เท่านั้น",
        "กฎสำคัญ: ใส่เฉพาะฟิลด์ที่มีข้อมูลรองรับจากคำบอกเล่าจริงๆ ห้ามเดา/ห้ามสร้างตัวเลขที่ไม่มีมูล",
        "ถ้าคำบอกเล่ามีอะไรที่เป็นความเสี่ยง (เช่น เปิด SMB1.0, license ใกล้หมดอายุ, hardware เก่า) ให้ใส่ลงใน health.critical_alerts ด้วยเสมอ แม้ผู้ใช้จะไม่ได้บอกตรงๆ ว่ามันเสี่ยง",
        "ตอบกลับเป็น YAML ก้อนเดียวเท่านั้น ครอบด้วย ```yaml ... ``` ไม่ต้องมีข้อความอื่นนอกก้อนโค้ด",
        "",
        "=== SCHEMA (มีคอมเมนต์อธิบายแต่ละฟิลด์) ===",
        schema,
        "",
        "=== ข้อมูลปัจจุบันของเดือนนี้ (อย่าซ้ำข้อมูลที่มีอยู่แล้ว เว้นแต่ต้องแก้ไข) ===",
        currentYaml,
        "",
        "=== รายละเอียดที่ผู้ใช้เล่า ===",
        aiNotes,
      ].join("\n");
      const r = await api.aiAssist(aiTool, prompt);
      setAiOutput(r.output);
      const parsed = extractYaml(r.output);
      setAiParsed(parsed);
      if (!parsed) setToast("AI ตอบมาแต่แปลงเป็น YAML ไม่ได้ — อ่าน raw output แล้ว copy เองด้านล่าง");
    } catch (e) {
      setToast(String(e));
    } finally {
      setBusy(null);
    }
  }

  function applyAiSuggestion() {
    if (!data || !aiParsed) return;
    setData(deepMerge(data, aiParsed));
    setDirty(true);
    setAiParsed(null);
    setAiOutput(null);
    setAiNotes("");
    setToast("นำข้อมูลที่ AI แนะนำเข้าฟอร์มแล้ว — ตรวจสอบและกด Save");
  }

  const alertCount = data ? computeAlertCount(data) : 0;

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 5000);
    return () => clearTimeout(t);
  }, [toast]);

  if (!currentClient || !data) {
    return (
      <div className="app-loading">
        {clients.length === 0 && !showNewClientForm ? (
          <div>
            <p>ยังไม่มีลูกค้าเลย — เริ่มสร้างลูกค้ารายแรก</p>
            <Button variant="primary" onClick={() => setShowNewClientForm(true)}>+ ลูกค้าใหม่</Button>
          </div>
        ) : showNewClientForm || clients.length === 0 ? (
          <NewClientForm
            code={newClientCode}
            name={newClientName}
            setCode={setNewClientCode}
            setName={setNewClientName}
            onCreate={handleCreateClient}
            busy={busy === "creating-client"}
          />
        ) : currentClient && months.length === 0 ? (
          <div>
            <p>ลูกค้า "{currentClient}" ยังไม่มีเดือนไหนเลย — สร้างเดือนแรก</p>
            <NewMonthForm
              newKey={newKey}
              newMonthName={newMonthName}
              setNewKey={setNewKey}
              setNewMonthName={setNewMonthName}
              onCreate={handleCreateMonth}
              busy={busy === "creating"}
            />
          </div>
        ) : (
          <p>กำลังโหลด…</p>
        )}
      </div>
    );
  }

  return (
    <div className="app">
      <header className="topbar">
        <h1>📊 IT Service Monthly Report</h1>
        <div className="topbar-controls">
          <select value={currentClient} onChange={(e) => setCurrentClient(e.target.value)}>
            {clients.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <Button variant="ghost" onClick={() => setShowNewClientForm((v) => !v)}>+ ลูกค้าใหม่</Button>
          <select value={currentFile ?? ""} onChange={(e) => loadFile(e.target.value)}>
            {months.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
          <Button variant="ghost" onClick={() => setShowNewForm((v) => !v)}>+ เดือนใหม่</Button>
          <Button onClick={handleSave} disabled={!dirty || busy === "saving"}>
            {busy === "saving" ? "กำลังบันทึก…" : dirty ? "Save*" : "Saved"}
          </Button>
          <Button variant="primary" onClick={handleGenerate} disabled={busy === "generating"}>
            {busy === "generating" ? "กำลังสร้าง…" : "Generate Report"}
          </Button>
        </div>
      </header>

      {showNewClientForm && (
        <div className="new-month-bar">
          <NewClientForm
            code={newClientCode}
            name={newClientName}
            setCode={setNewClientCode}
            setName={setNewClientName}
            onCreate={handleCreateClient}
            busy={busy === "creating-client"}
          />
        </div>
      )}

      {showNewForm && (
        <div className="new-month-bar">
          <NewMonthForm
            newKey={newKey}
            newMonthName={newMonthName}
            setNewKey={setNewKey}
            setNewMonthName={setNewMonthName}
            onCreate={handleCreateMonth}
            busy={busy === "creating"}
          />
        </div>
      )}

      <div className="status-bar">
        <StatusPill status={data.health.overall_status} />
        <span className="status-item">Client: {data.report.client_name ?? "⚠️ MISSING"}</span>
        <span className="status-item">{data.report.month} {data.report.year}</span>
        {alertCount > 0 && <span className="status-item alert-badge">⚠️ {alertCount} critical alert{alertCount > 1 ? "s" : ""}</span>}
        {changelog.length > 0 && (
          <span className="status-item">📝 {changelog.length} changes since {changelogPrevMonth}</span>
        )}
        <Button variant="ghost" onClick={() => setPreflightOpen((v) => !v)}>
          🔍 Pre-flight {preflightOpen ? "▲" : "▼"}
        </Button>
        <Button variant="ghost" onClick={() => setAiOpen((v) => !v)}>
          🤖 AI ช่วยวิเคราะห์ {aiOpen ? "▲" : "▼"}
        </Button>
      </div>

      {preflightOpen && (
        <div className="ai-panel">
          <p className="field-label">Pre-flight readiness check (ไม่บล็อกการ Generate — แค่เตือน):</p>
          <ul className="preflight-list">
            {computePreflight(data).map((item, i) => (
              <li key={i} className={item.ok ? "preflight-ok" : "preflight-warn"}>
                {item.ok ? "✅" : "⚠️"} {item.label}
              </li>
            ))}
          </ul>
        </div>
      )}

      {changelog.length > 0 && (
        <div className="ai-panel">
          <p className="field-label">Changes since {changelogPrevMonth}:</p>
          <ul>
            {changelog.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      )}

      {aiOpen && (
        <div className="ai-panel">
          <div className="ai-panel-row">
            <select value={aiTool} onChange={(e) => setAiTool(e.target.value as "zcode" | "agy")}>
              <option value="agy">agy (Gemini)</option>
              <option value="zcode">zcode (GLM)</option>
            </select>
            <textarea
              placeholder="เล่ารายละเอียดเดือนนี้ เช่น: ย้าย Express ไป desktop ใหม่, backup ปกติ, M365 จะหมดอายุอาทิตย์หน้า..."
              rows={3}
              value={aiNotes}
              onChange={(e) => setAiNotes(e.target.value)}
            />
            <Button variant="primary" onClick={handleAiAssist} disabled={busy === "ai" || !aiNotes.trim()}>
              {busy === "ai" ? "กำลังวิเคราะห์… (อาจใช้เวลาหลายนาที)" : "วิเคราะห์"}
            </Button>
          </div>
          {aiOutput && (
            <div className="ai-output">
              {aiParsed ? (
                <>
                  <p className="ai-output-status">✅ แปลงเป็นข้อมูลได้ — ตรวจสอบก่อนนำเข้า:</p>
                  <pre className="ai-preview">{yaml.dump(aiParsed, { lineWidth: 100 })}</pre>
                  <Button variant="primary" onClick={applyAiSuggestion}>นำเข้าข้อมูลนี้เข้าฟอร์ม</Button>
                </>
              ) : (
                <>
                  <p className="ai-output-status">⚠️ แปลงเป็น YAML อัตโนมัติไม่ได้ — นี่คือคำตอบดิบจาก AI:</p>
                  <pre className="ai-preview">{aiOutput}</pre>
                </>
              )}
            </div>
          )}
        </div>
      )}

      <div className="app-body">
        <nav className="sidebar">
          {SECTIONS.map((s) => (
            <button key={s.id} className={`nav-item ${section === s.id ? "active" : ""}`} onClick={() => setSection(s.id)}>
              {s.label}
            </button>
          ))}
        </nav>
        <main className="content">
          {section === "meta" && <MetaSection data={data} set={set} />}
          {section === "exec" && <ExecutiveSection data={data} set={set} />}
          {section === "computers" && <ComputersSection data={data} set={set} />}
          {section === "software" && <SoftwareSection data={data} set={set} />}
          {section === "server" && <ServerSection data={data} set={set} />}
          {section === "infra" && <InfraSection data={data} set={set} />}
          {section === "tickets" && <TicketsSection data={data} set={set} onError={setToast} />}
          {section === "scope" && <ScopeSection data={data} set={set} />}
          {section === "recs" && <RecommendationsSection data={data} set={set} />}
        </main>
      </div>

      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}

function NewMonthForm({
  newKey,
  newMonthName,
  setNewKey,
  setNewMonthName,
  onCreate,
  busy,
}: {
  newKey: string;
  newMonthName: string;
  setNewKey: (v: string) => void;
  setNewMonthName: (v: string) => void;
  onCreate: () => void;
  busy: boolean;
}) {
  return (
    <div className="new-month-form">
      <input placeholder="File key เช่น 2026-08" value={newKey} onChange={(e) => setNewKey(e.target.value)} />
      <input placeholder="ชื่อเดือน เช่น August" value={newMonthName} onChange={(e) => setNewMonthName(e.target.value)} />
      <Button variant="primary" onClick={onCreate} disabled={busy || !newKey.trim()}>
        {busy ? "กำลังสร้าง…" : "สร้างเดือนใหม่ (auto carry-forward)"}
      </Button>
    </div>
  );
}

function NewClientForm({
  code,
  name,
  setCode,
  setName,
  onCreate,
  busy,
}: {
  code: string;
  name: string;
  setCode: (v: string) => void;
  setName: (v: string) => void;
  onCreate: () => void;
  busy: boolean;
}) {
  return (
    <div className="new-month-form">
      <input placeholder="รหัสลูกค้า เช่น kittisampan" value={code} onChange={(e) => setCode(e.target.value)} />
      <input placeholder="ชื่อลูกค้าเต็ม" value={name} onChange={(e) => setName(e.target.value)} />
      <Button variant="primary" onClick={onCreate} disabled={busy || !code.trim() || !name.trim()}>
        {busy ? "กำลังสร้าง…" : "สร้างลูกค้าใหม่"}
      </Button>
    </div>
  );
}
