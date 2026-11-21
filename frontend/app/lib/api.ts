// 백엔드(FastAPI) 호출. 요청·응답 모양은 docs/api-contract.md 2·3장을 따른다.
import type { Course } from "./courses";
import type { PlanningConstraints } from "./planning";
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
  track: string | null; grade: number | null; completed: string[]; max_candidates: number;
};

/** 저장된 조건 + 학생 정보 + 이수 체크 → POST /tools/generate_timetable 요청 본문. */
export function buildGenerateRequest(planning: PlanningConstraints, student: StudentProfile, completedCourses: Course[]): GenerateTimetableRequest {
  const track = computingMajors.some(major => major.id === student.majorId) ? student.majorId : null;
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
export type PlanChatResponse = { reply: string; applied: boolean; request: GenerateTimetableRequest; response: GenerateTimetableResponse | null };

/** 나의 시간표 챗봇. message 가 없으면 지금 후보를 설명만 하고, 있으면 말대로 고친 시간표를 돌려준다. */
export function chatTimetable(body: { message: string | null; request: GenerateTimetableRequest; candidate_id: string | null; history: ChatTurn[] }, signal?: AbortSignal) {
  return request<PlanChatResponse>("/tools/chat", { method: "POST", body: JSON.stringify(body), signal });
}
