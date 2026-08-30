import yaml from "js-yaml";

// Merge AI-suggested partial data into the current form state.
// Rule: never silently overwrite a value the human already filled in.
// - scalars: keep current value if it's non-empty; otherwise take the AI's.
// - object arrays (tickets, alerts, licenses, ...): append AI entries that
//   aren't already present (dedup by JSON equality) — additive, not replacing.
// - primitive arrays (highlights, recurring_issues): same, string-based union.
function isEmpty(v: unknown): boolean {
  return v === null || v === undefined || v === "" || (Array.isArray(v) && v.length === 0);
}

export function deepMerge<T>(current: T, incoming: unknown): T {
  if (incoming === null || incoming === undefined) return current;

  if (Array.isArray(current)) {
    const incomingArr = Array.isArray(incoming) ? incoming : [];
    const existingKeys = new Set(current.map((x) => JSON.stringify(x)));
    const additions = incomingArr.filter((x) => !existingKeys.has(JSON.stringify(x)));
    return [...current, ...additions] as unknown as T;
  }

  if (typeof current === "object" && current !== null && typeof incoming === "object") {
    const result: Record<string, unknown> = { ...(current as Record<string, unknown>) };
    for (const key of Object.keys(incoming as Record<string, unknown>)) {
      const incomingVal = (incoming as Record<string, unknown>)[key];
      const currentVal = (current as Record<string, unknown>)[key];
      result[key] =
        currentVal === undefined ? incomingVal : deepMerge(currentVal, incomingVal);
    }
    return result as T;
  }

  return isEmpty(current) && !isEmpty(incoming) ? (incoming as T) : current;
}

/** Extract the first ```yaml ... ``` fenced block, or try parsing the whole string. */
export function extractYaml(text: string): unknown | null {
  const fenced = text.match(/```ya?ml\s*([\s\S]*?)```/i);
  const candidate = fenced ? fenced[1] : text;
  try {
    return yaml.load(candidate.trim());
  } catch {
    return null;
  }
}
