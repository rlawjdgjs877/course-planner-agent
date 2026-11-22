export const planningDays = ["월", "화", "수", "목", "금", "토"] as const;
export type PlanningDay = typeof planningDays[number];
export type TimeConstraint = { day: PlanningDay; start: string; end: string };
export type PlanningConstraints = {
  base_candidate_id: string | null; min_credits: number; target_credits: number; max_credits: number;
  credits_strict: boolean; free_days: PlanningDay[]; blocked_times: TimeConstraint[]; avoid_times: TimeConstraint[];
  must_include: string[]; exclude: string[]; ge_areas: string[]; prefer_professor: string[];
  /** true 면 토·일 수업도 자동 추천한다 */ allow_weekend: boolean;
};
export const defaultPlanning: PlanningConstraints = {
  base_candidate_id: null, min_credits: 15, target_credits: 18, max_credits: 19, credits_strict: false,
  free_days: [], blocked_times: [], avoid_times: [], must_include: [], exclude: [], ge_areas: [], prefer_professor: [], allow_weekend: false,
};
export function timeMinutes(value: string) {
  const match = /^(\d{2}):(\d{2})$/.exec(value);
  if (!match) return null;
  const hour = Number(match[1]), minute = Number(match[2]);
  return hour <= 23 && minute <= 59 ? hour * 60 + minute : hour === 24 && minute === 0 ? 1440 : null;
}
export function validTimeConstraint(value: unknown): value is TimeConstraint {
  if (!value || typeof value !== "object") return false;
  const block = value as TimeConstraint;
  const start = typeof block.start === "string" ? timeMinutes(block.start) : null;
  const end = typeof block.end === "string" ? timeMinutes(block.end) : null;
  return planningDays.includes(block.day) && start !== null && end !== null && start < end;
}
export function validatePlanning(value: PlanningConstraints): string[] {
  const errors: string[] = [];
  if (![value.min_credits, value.target_credits, value.max_credits].every(n => Number.isInteger(n) && n >= 0 && n <= 30)) errors.push("학점은 0~30 사이 정수로 입력해 주세요. 실제 상한은 학칙을 확인해야 합니다.");
  if (value.min_credits > value.target_credits || value.target_credits > value.max_credits) errors.push("최소 학점 ≤ 목표 학점 ≤ 최대 학점 순서로 입력해 주세요.");
  if ([...value.blocked_times, ...value.avoid_times].some(block => !validTimeConstraint(block))) errors.push("시간대의 요일과 시작·종료 시각을 확인해 주세요. 종료는 시작보다 늦어야 합니다.");
  const excludes = new Set(value.exclude);
  if (value.must_include.some(id => excludes.has(id) || excludes.has(id.replace(/-\d+$/, "")))) errors.push("반드시 포함할 과목과 제외할 과목이 겹칩니다.");
  return errors;
}
export function restorePlanning(input: unknown, legacyCredits?: unknown, legacyFreeDay?: unknown): PlanningConstraints {
  const result: PlanningConstraints = { ...defaultPlanning, free_days: [], blocked_times: [], avoid_times: [], must_include: [], exclude: [], ge_areas: [], prefer_professor: [] };
  if (!input || typeof input !== "object") {
    if (typeof legacyCredits === "number" && Number.isInteger(legacyCredits) && legacyCredits >= 0 && legacyCredits <= 30) { result.target_credits = legacyCredits; result.min_credits = Math.min(15, legacyCredits); result.max_credits = Math.max(19, legacyCredits); }
    if (planningDays.includes(legacyFreeDay as PlanningDay)) result.avoid_times = [{ day: legacyFreeDay as PlanningDay, start: "00:00", end: "23:59" }];
    return result;
  }
  const data = input as Record<string, unknown>;
  for (const key of ["min_credits", "target_credits", "max_credits"] as const) if (typeof data[key] === "number" && Number.isInteger(data[key]) && data[key] >= 0 && data[key] <= 30) result[key] = data[key];
  result.credits_strict = data.credits_strict === true;
  result.allow_weekend = data.allow_weekend === true;
  for (const key of ["must_include", "exclude", "ge_areas", "prefer_professor"] as const) if (Array.isArray(data[key])) result[key] = [...new Set(data[key].filter((v): v is string => typeof v === "string" && v.length <= 100))].slice(0, 100);
  if (Array.isArray(data.free_days)) result.free_days = [...new Set(data.free_days.filter((day): day is PlanningDay => planningDays.includes(day as PlanningDay)))];
  for (const key of ["blocked_times", "avoid_times"] as const) if (Array.isArray(data[key])) result[key] = data[key].filter(validTimeConstraint).slice(0, 30).map(({ day, start, end }) => ({ day, start, end }));
  // Candidate IDs belong to a backend session; never restore them into another session.
  return result;
}
export type ParsedMeeting = { day: string; start: number; end: number };
export function parseMeetingTimes(raw: string): ParsedMeeting[] | null {
  if (!raw.trim()) return null;
  const meetings: ParsedMeeting[] = [];
  for (const part of raw.split(",")) {
    const match = /^\s*([월화수목금토일])\s+(\d{1,2}:\d{2})\s*~\s*(\d{1,2}:\d{2})\s*$/.exec(part);
    if (!match) return null;
    const start = timeMinutes(match[2].padStart(5, "0")), end = timeMinutes(match[3].padStart(5, "0"));
    if (start === null || end === null || start >= end) return null;
    meetings.push({ day: match[1], start, end });
  }
  return meetings;
}
export type PlannedSection = { id: string; code: string; name: string; time: string; inconsistent?: boolean };
export function checkSectionConflicts(sections: PlannedSection[]) {
  const unresolved = sections.filter(s => s.inconsistent || !parseMeetingTimes(s.time)).map(s => s.id);
  const duplicate_courses: { code: string; sections: string[] }[] = [];
  const conflicts: { a: string; b: string; day: string; start: number; end: number }[] = [];
  const codes = new Map<string, string[]>();
  for (const section of sections) codes.set(section.code, [...(codes.get(section.code) ?? []), section.id]);
  for (const [code, ids] of codes) if (ids.length > 1) duplicate_courses.push({ code, sections: ids });
  for (let i = 0; i < sections.length; i++) for (let j = i + 1; j < sections.length; j++) {
    if (sections[i].inconsistent || sections[j].inconsistent) continue;
    const first = parseMeetingTimes(sections[i].time), second = parseMeetingTimes(sections[j].time);
    if (!first || !second) continue;
    for (const a of first) for (const b of second) if (a.day === b.day && a.start < b.end && b.start < a.end) conflicts.push({ a: sections[i].id, b: sections[j].id, day: a.day, start: Math.max(a.start, b.start), end: Math.min(a.end, b.end) });
  }
  return { ok: !unresolved.length && !duplicate_courses.length && !conflicts.length, conflicts, duplicate_courses, unresolved };
}
export const formatMinutes = (n: number) => `${String(Math.floor(n / 60)).padStart(2, "0")}:${String(n % 60).padStart(2, "0")}`;
