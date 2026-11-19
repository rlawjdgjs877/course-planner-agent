export type ImportedCourse = { code: string; name: string; credits: number | null; category: string | null };
export type CatalogCourse = { id: string; code?: string };
export function normalizeImportedCourses(input: unknown): ImportedCourse[] {
  if (!Array.isArray(input)) return [];
  const result = new Map<string, ImportedCourse>();
  for (const value of input.slice(0, 2000)) {
    if (!value || typeof value !== "object") continue;
    const row = value as Record<string, unknown>;
    if (typeof row.code !== "string" || typeof row.name !== "string") continue;
    const code = row.code.trim().toUpperCase(), name = row.name.trim();
    if (!/^[A-Z0-9]{2,40}$/.test(code) || !name || name.length > 200) continue;
    if (result.has(code)) continue;
    result.set(code, { code, name, credits: typeof row.credits === "number" && Number.isFinite(row.credits) && row.credits >= 0 && row.credits <= 30 ? row.credits : null, category: typeof row.category === "string" ? row.category.trim().slice(0, 100) || null : null });
  }
  return [...result.values()];
}
export function mergeImportedCourses(existing: ImportedCourse[], incoming: ImportedCourse[]) {
  return normalizeImportedCourses([...incoming, ...existing]);
}
export function importedCatalogIds(imported: ImportedCourse[], catalog: CatalogCourse[]) {
  const codes = new Set(imported.map(course => course.code));
  return catalog.filter(course => course.code && codes.has(course.code)).map(course => course.id);
}
