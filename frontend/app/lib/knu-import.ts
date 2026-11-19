import { normalizeImportedCourses, type ImportedCourse } from "./imported-courses";
export type KnuImportStatus = { enabled: boolean; installed: boolean; available: boolean; reason: string | null; idle_minutes: number };
export type KnuFrame = { image: string | null; frame_id: string | null; status: string; finished: boolean; login_form: boolean; needs_help: boolean; courses: ImportedCourse[]; duplicates: string[]; expires_in: number };
export type KnuInput = { type: "click"; x: number; y: number } | { type: "key"; key: string } | { type: "text"; text: string } | { type: "scroll"; delta: number };
export class KnuApiError extends Error { constructor(message: string, public status = 0) { super(message); } }
export function knuApiBase() {
  const configured = process.env.NEXT_PUBLIC_API_BASE?.trim();
  const localHost = typeof window !== "undefined" && ["localhost", "127.0.0.1", "[::1]"].includes(window.location.hostname);
  const raw = configured || (localHost ? "http://localhost:8000" : "");
  if (!raw) throw new KnuApiError("학교 불러오기 서버가 연결되지 않았습니다. 직접 입력을 이용하거나 운영자에게 서버 연결을 요청해 주세요.");
  let url: URL;
  try { url = new URL(raw); } catch { throw new KnuApiError("학교 불러오기 서버 주소가 올바르지 않습니다."); }
  const loopback = ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname);
  if (url.username || url.password || url.search || url.hash || (url.protocol !== "https:" && !(url.protocol === "http:" && loopback))) throw new KnuApiError("학교 불러오기는 HTTPS 서버 또는 이 컴퓨터의 로컬 서버에서 연결해야 합니다.");
  return url.href.replace(/\/$/, "");
}
export async function knuRequest<T>(path: string, body?: unknown, session?: string, signal?: AbortSignal): Promise<T> {
  const base = knuApiBase();
  let response: Response;
  try {
    response = await fetch(`${base}/import/knu/${path}`, { method: body === undefined ? "GET" : "POST", credentials: "omit", cache: "no-store", signal: signal ?? AbortSignal.timeout(30000), headers: { ...(body === undefined ? {} : { "Content-Type": "application/json" }), ...(session ? { "X-Import-Session": session } : {}) }, ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") throw error;
    throw new KnuApiError("학교 불러오기 서버에 연결하지 못했습니다. 백엔드 실행 상태를 확인해 주세요.");
  }
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data && typeof data === "object" && "detail" in data && typeof data.detail === "string" ? data.detail : `학교 화면 요청에 실패했습니다 (${response.status}).`;
    throw new KnuApiError(detail, response.status);
  }
  return data as T;
}
export function parseKnuFrame(value: unknown): KnuFrame {
  if (!value || typeof value !== "object") throw new KnuApiError("학교 화면 응답 형식을 확인할 수 없습니다.");
  const data = value as Record<string, unknown>;
  if (typeof data.status !== "string" || typeof data.finished !== "boolean") throw new KnuApiError("학교 화면 응답 형식이 올바르지 않습니다.");
  return { image: typeof data.image === "string" && data.image.length <= 8_000_000 && /^[A-Za-z0-9+/=\r\n]+$/.test(data.image) ? data.image : null, frame_id: typeof data.frame_id === "string" ? data.frame_id : null, status: data.status.slice(0, 1000), finished: data.finished, login_form: data.login_form === true, needs_help: data.needs_help === true, courses: normalizeImportedCourses(data.courses), duplicates: Array.isArray(data.duplicates) ? data.duplicates.filter((code): code is string => typeof code === "string").slice(0, 2000) : [], expires_in: typeof data.expires_in === "number" ? data.expires_in : 0 };
}
export async function closeKnuSession(session: string, keepalive = false) {
  try { const response = await fetch(`${knuApiBase()}/import/knu/stop`, { method: "POST", credentials: "omit", cache: "no-store", keepalive, headers: { "Content-Type": "application/json", "X-Import-Session": session }, body: JSON.stringify({ session }) }); return response.ok; } catch { return false; }
}
