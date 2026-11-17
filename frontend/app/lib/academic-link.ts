export function normalizeAcademicLink(input: unknown): string {
  if (typeof input !== "string" || input.trim().length > 2048) return "";
  try {
    const url = new URL(input.trim());
    if (!["https:", "http:"].includes(url.protocol) || url.username || url.password) return "";
    return url.href;
  } catch { return ""; }
}
