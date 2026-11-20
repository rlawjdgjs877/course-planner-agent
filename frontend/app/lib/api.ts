// 백엔드(FastAPI) 호출. 요청·응답 모양은 docs/api-contract.md 2·3장을 따른다.
import type { Course } from "./courses";
import { planningDays, type PlanningConstraints, type PlanningDay } from "./planning";
import type { StudentProfile } from "./student-profile";
import { computingMajors } from "./student-profile";

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
};
export type OmittedCourse = { item: string; code: string | null; name: string | null; reason: string; detail: string };
export type Alternative = { id: string; relaxed: string[]; description: string; candidate: Candidate };
export type GenerateTimetableResponse = {
  status: "success" | "partial" | "infeasible"; optimal: boolean; candidates: Candidate[];
  applied: Record<string, unknown>; omitted_required: OmittedCourse[]; warnings: string[]; alternatives: Alternative[];
};
export type GenerateTimetableRequest = PlanningConstraints & {
  track: string | null; grade: number | null; completed: string[]; completed_names: string[]; max_candidates: number;
};

/** 저장된 조건 + 학생 정보 + 이수 과목(체크·학교에서 불러온 것) → POST /tools/generate_timetable 요청 본문. */
export function buildGenerateRequest(planning: PlanningConstraints, student: StudentProfile, completedCourses: Pick<Course, "name" | "code">[]): GenerateTimetableRequest {
  const track = computingMajors.some(major => major.id === student.majorId) ? student.majorId : null;
  const grade = Number(student.currentGrade);
  // 백엔드는 과목코드를 기대한다. 코드가 없는 과목은 과목명으로 보내면 백엔드가 이름으로 찾는다.
  const completed = [...new Set(completedCourses.map(course => course.code || course.name))];
  // 과목명은 선수과목(학과 권장 순서) 확인에 쓴다. 이번 학기에 열리지 않는 과목은 코드만으로 이름을 알 수 없다.
  const completed_names = [...new Set(completedCourses.map(course => course.name))];
  return { ...planning, track, grade: Number.isInteger(grade) && grade >= 1 && grade <= 6 ? grade : null, completed, completed_names, max_candidates: 3 };
}

/** 에이전트가 고친 조건(백엔드 형식)을 화면의 조건으로 되돌린다. 학생 정보와 이수 과목은 화면 것을 그대로 쓴다. */
export function planningFromRequest(request: GenerateTimetableRequest, previous: PlanningConstraints): PlanningConstraints {
  const days = planningDays as readonly string[];
  const blocks = (items: { day: string; start: string; end: string }[]) => items.filter(b => days.includes(b.day)).map(b => ({ day: b.day as PlanningDay, start: b.start, end: b.end === "24:00" ? "23:59" : b.end }));
  return {
    ...previous,
    min_credits: request.min_credits, target_credits: request.target_credits, max_credits: request.max_credits, credits_strict: request.credits_strict,
    free_days: request.free_days.filter((d): d is PlanningDay => days.includes(d)),
    blocked_times: blocks(request.blocked_times), avoid_times: blocks(request.avoid_times),
    must_include: request.must_include, exclude: request.exclude, ge_areas: request.ge_areas, prefer_professor: request.prefer_professor,
  };
}

export type AgentStep = { tool: string; label: string; ok: boolean };
export type AgentMessage = { role: "user" | "assistant"; content: string };
export type AgentChatResponse = { reply: string; steps: AgentStep[]; applied: boolean; request: GenerateTimetableRequest; result: GenerateTimetableResponse | null };

export function agentChat(body: { mode: "chat" | "summary"; message: string; request: GenerateTimetableRequest; candidate_id: string | null; history: AgentMessage[] }, signal?: AbortSignal) {
  return request<AgentChatResponse>("/agent/chat", { method: "POST", body: JSON.stringify(body), signal });
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
