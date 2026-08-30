import React from "react";

export function Card({ title, children, right }: { title?: string; children: React.ReactNode; right?: React.ReactNode }) {
  return (
    <div className="card">
      {title && (
        <div className="card-head">
          <h3>{title}</h3>
          {right}
        </div>
      )}
      {children}
    </div>
  );
}

export function Field({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
}: {
  label: string;
  value: string | number | null;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      <input
        type={type}
        value={value ?? ""}
        placeholder={placeholder ?? "—"}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}

export function NumberField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number | null;
  onChange: (v: number | null) => void;
}) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      <input
        type="number"
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value === "" ? null : Number(e.target.value))}
      />
    </label>
  );
}

export function TextArea({
  label,
  value,
  onChange,
  rows = 3,
}: {
  label: string;
  value: string | null;
  onChange: (v: string) => void;
  rows?: number;
}) {
  return (
    <label className="field field-wide">
      <span className="field-label">{label}</span>
      <textarea rows={rows} value={value ?? ""} onChange={(e) => onChange(e.target.value)} />
    </label>
  );
}

export function Select<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T | null;
  options: { value: T; label: string }[];
  onChange: (v: T) => void;
}) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      <select value={value ?? ""} onChange={(e) => onChange(e.target.value as T)}>
        <option value="" disabled>
          — เลือก —
        </option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}

const STATUS_META: Record<string, { icon: string; label: string; className: string }> = {
  green: { icon: "🟢", label: "Normal", className: "pill-green" },
  yellow: { icon: "🟡", label: "Warning", className: "pill-yellow" },
  red: { icon: "🔴", label: "Critical", className: "pill-red" },
  normal: { icon: "🟢", label: "Normal", className: "pill-green" },
  ok: { icon: "🟢", label: "OK", className: "pill-green" },
  warning: { icon: "🟡", label: "Warning", className: "pill-yellow" },
  caution: { icon: "🟡", label: "Caution", className: "pill-yellow" },
  critical: { icon: "🔴", label: "Critical", className: "pill-red" },
  issue: { icon: "🔴", label: "Issue", className: "pill-red" },
};

export function StatusPill({ status }: { status: string | null | undefined }) {
  if (!status) return <span className="pill pill-missing">⚠️ MISSING</span>;
  const meta = STATUS_META[status.toLowerCase()] ?? { icon: "•", label: status, className: "pill-neutral" };
  return (
    <span className={`pill ${meta.className}`}>
      {meta.icon} {meta.label}
    </span>
  );
}

export function Missing() {
  return <span className="pill pill-missing">⚠️ MISSING</span>;
}

export function Button({
  children,
  onClick,
  variant = "default",
  disabled,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: "default" | "primary" | "ghost";
  disabled?: boolean;
}) {
  return (
    <button className={`btn btn-${variant}`} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}
