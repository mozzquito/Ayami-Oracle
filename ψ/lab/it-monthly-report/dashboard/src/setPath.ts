export type Path = (string | number)[];

/** Immutable nested set: setPath(obj, ["a", "b", 0], value) */
export function setPath<T>(obj: T, path: Path, value: unknown): T {
  if (path.length === 0) return value as T;
  const [head, ...rest] = path;
  if (Array.isArray(obj)) {
    const copy = [...obj];
    copy[head as number] = setPath(copy[head as number], rest, value);
    return copy as unknown as T;
  }
  const copy = { ...(obj as Record<string, unknown>) };
  copy[head as string] = setPath(copy[head as string], rest, value);
  return copy as T;
}

export function getPath(obj: unknown, path: Path): unknown {
  return path.reduce((acc: any, key) => (acc == null ? acc : acc[key]), obj);
}
