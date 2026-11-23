// 백엔드(FastAPI) 호출. 요청·응답 모양은 docs/api-contract.md 2·3장을 따른다.
import type { Course } from "./courses";
import type { PlanningConstraints } from "./planning";
import type { StudentProfile } from "./student-profile";
import { computingMajors } from "./student-profile";

/** 공개 체험판(Vercel 등)으로 배포할 때 1. 학교 로그인 대신 샘플 학생·직접 체크로 시작한다. */
export const PUBLIC_DEMO = process.env.NEXT_PUBLIC_PUBLIC_DEMO === "1";

export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000").replace(/\/+$/, "");

export type ApiMeeting = { day: string; start: string; end: string };
export type ApiSection = {
  course_id: string; course_code: string; section: string | null; name: string; credits: number;
  professor: string | null; category: string; grade: string | null; area: string | null;
  meetings: ApiMeeting[]; time_raw: string | null; building: string | null; room: string | null;
  capacity: number | null; enrolled: number | null;
};
export type Candidate = {
  id: string; sections: ApiSection[]; total_credits: number; credits_by_category: Record<string, number>;
  free_days: string[]; gap_minutes: number; score: number; warnings: string[];
  /** 선수과목 확인 결과. 예전 백엔드에는 없을 수 있다. */
  prereq_issues?: PrereqIssue[];
};
export type PrereqIssue = { course_id: string; name: string; missing: string[]; chain: string; page: number; kind: "missing" | "concurrent" };
export type OmittedCourse = { item: string; code: string | null; name: string | null; reason: string; detail: string };
export type Alternative = { id: string; relaxed: string[]; description: string; candidate: Candidate };
export type GenerateTimetableResponse = {
  status: "success" | "partial" | "infeasible"; optimal: boolean; candidates: Candidate[];
  applied: Record<string, unknown>; omitted_required: OmittedCourse[]; warnings: string[]; alternatives: Alternative[];
};
export type GenerateTimetableRequest = PlanningConstraints & {
  track: string | null; grade: number | null; completed: string[]; max_candidates: number;
};

const backendTrack: Record<string, string> = { advanced: "advanced", ai: "ai", research: "research", platform: "platform", global: "global" };

/** 저장된 조건 + 학생 정보 + 이수 체크 → POST /tools/generate_timetable 요청 본문. */
export function buildGenerateRequest(planning: PlanningConstraints, student: StudentProfile, completedCourses: Course[]): GenerateTimetableRequest {
  // 백엔드 planner.TRACKS 의 키로 맞춘다 (백엔드도 별칭을 받지만, 보낼 때부터 정식 키로 보낸다).
  const track = computingMajors.some(major => major.id === student.majorId) ? backendTrack[student.majorId] ?? null : null;
  const grade = Number(student.currentGrade);
  // 백엔드는 과목코드를 기대한다. 코드가 없는 과목은 과목명으로 보내면 백엔드가 이름으로 찾는다.
  const completed = [...new Set(completedCourses.map(course => course.code || course.name))];
  return { ...planning, track, grade: Number.isInteger(grade) && grade >= 1 && grade <= 6 ? grade : null, completed, max_candidates: 3 };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, { ...init, headers: { "Content-Type": "application/json", ...init?.headers } });
  } catch (error) {
    if (init?.signal?.aborted) throw error;
    throw new Error(`백엔드(${API_BASE})에 연결하지 못했습니다. 서버가 켜져 있는지 확인해 주세요.`);
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body?.detail;
    const message = typeof detail === "string" ? detail : Array.isArray(detail) ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(" / ") : "";
    throw new Error(message || `요청이 실패했습니다 (HTTP ${response.status}).`);
  }
  return body as T;
}

export function generateTimetable(body: GenerateTimetableRequest, signal?: AbortSignal) {
  return request<GenerateTimetableResponse>("/tools/generate_timetable", { method: "POST", body: JSON.stringify(body), signal });
}

export function fetchCandidate(id: string, signal?: AbortSignal) {
  return request<Candidate>(`/tools/candidates/${encodeURIComponent(id)}`, { signal });
}

export type ChatTurn = { role: "user" | "assistant"; content: string };
/** 챗봇 에이전트가 거친 단계 하나 (도구 호출). */
export type AgentStep = { tool: string; label: string; detail: string; ok: boolean };
export type PlanChatResponse = {
  reply: string; applied: boolean; request: GenerateTimetableRequest; response: GenerateTimetableResponse | null;
  // 아래는 새 백엔드에만 있다. 없을 때도 화면이 깨지지 않게 optional 로 둔다.
  steps?: AgentStep[]; mode?: "ai" | "rules"; previous_candidate_id?: string | null;
  /** 이 후보 탭을 보여 달라는 뜻 (예 "tt_002"). */
  select_candidate?: string | null;
};

/** 나의 시간표 챗봇. message 가 없으면 지금 후보를 설명만 하고, 있으면 말대로 고친 시간표를 돌려준다. */
export function chatTimetable(body: { message: string | null; request: GenerateTimetableRequest; candidate_id: string | null; candidate_ids: string[]; history: ChatTurn[] }, signal?: AbortSignal) {
  return request<PlanChatResponse>("/tools/chat", { method: "POST", body: JSON.stringify(body), signal });
}

/** 무료 호스팅 서버는 한동안 안 쓰면 잠든다. 첫 화면에서 미리 깨워 둔다 (실패해도 무시). */
export function wakeBackend() {
  fetch(`${API_BASE}/health`).catch(() => undefined);
}
