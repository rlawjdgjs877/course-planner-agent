// 학교 졸업자가진단에서 읽어 온 학생 정보와 교과구분별 이수 현황.
// 이름·학번·연락처 같은 개인정보는 백엔드에서 이미 뺐고, 여기서도 아래 칸만 받는다.
import { computingMajors, type StudentProfile } from "./student-profile";

export type SchoolStudent = {
  grade: number | null; department: string | null; track: string | null; admission_year: string | null;
  status: string | null; admission_type: string | null; campus: string | null; curriculum_year: string | null;
  semesters: number | null; math_exempt: boolean | null; teaching: boolean | null; other_major: string | null;
  gpa: number | null; total_credits: number | null;
};
export type CreditStatus = {
  name: string; group: string | null; major: string | null; required: number | null; earned: number | null;
  confirmed: number | null; in_progress: number | null; satisfied: boolean | null; shortage: number | null; area: string | null;
};
export type EssentialCourse = { code: string | null; name: string; credits: number | null; state: "done" | "taking" | "missing" | "failed"; major: string | null };
export type Certification = { area: string; passed: boolean | null; exempt: boolean | null };
export type SchoolDiagnosis = { student: SchoolStudent | null; requirements: CreditStatus[]; required_courses: EssentialCourse[]; certifications: Certification[]; ge_shortage: string[] };

const str = (v: unknown, max = 100) => typeof v === "string" && v.trim() ? v.trim().slice(0, max) : null;
const num = (v: unknown) => typeof v === "number" && Number.isFinite(v) ? v : null;
const bool = (v: unknown) => typeof v === "boolean" ? v : null;
const year = (v: unknown) => typeof v === "string" && /^(19|20)\d{2}$/.test(v) ? v : null;
const obj = (v: unknown) => v && typeof v === "object" && !Array.isArray(v) ? v as Record<string, unknown> : null;
const list = (v: unknown, max: number) => Array.isArray(v) ? v.slice(0, max).map(obj).filter((x): x is Record<string, unknown> => !!x) : [];
const STATES = ["done", "taking", "missing", "failed"] as const;

export function parseSchoolDiagnosis(value: unknown): SchoolDiagnosis | null {
  const data = obj(value);
  if (!data) return null;
  const s = obj(data.student);
  const grade = num(s?.grade);
  const student: SchoolStudent | null = s ? {
    grade: grade !== null && Number.isInteger(grade) && grade >= 1 && grade <= 6 ? grade : null,
    department: str(s.department), track: computingMajors.some(m => m.id === s.track) ? s.track as string : null,
    admission_year: year(s.admission_year), status: str(s.status, 30), admission_type: str(s.admission_type, 30), campus: str(s.campus, 30),
    curriculum_year: year(s.curriculum_year), semesters: num(s.semesters), math_exempt: bool(s.math_exempt), teaching: bool(s.teaching),
    other_major: str(s.other_major, 80), gpa: num(s.gpa), total_credits: num(s.total_credits),
  } : null;
  const requirements: CreditStatus[] = list(data.requirements, 80).flatMap(r => {
    const name = str(r.name, 60);
    return name ? [{ name, group: str(r.group, 30), major: str(r.major, 30), required: num(r.required), earned: num(r.earned), confirmed: num(r.confirmed), in_progress: num(r.in_progress), satisfied: bool(r.satisfied), shortage: num(r.shortage), area: str(r.area, 30) }] : [];
  });
  const required_courses: EssentialCourse[] = list(data.required_courses, 100).flatMap(c => {
    const name = str(c.name);
    const state = STATES.find(x => x === c.state);
    return name && state ? [{ code: str(c.code, 20), name, credits: num(c.credits), state, major: str(c.major, 30) }] : [];
  });
  const certifications: Certification[] = list(data.certifications, 30).flatMap(c => {
    const area = str(c.area, 60);
    return area ? [{ area, passed: bool(c.passed), exempt: bool(c.exempt) }] : [];
  });
  const ge_shortage = Array.isArray(data.ge_shortage) ? [...new Set(data.ge_shortage.filter((x): x is string => typeof x === "string" && x.length <= 30))].slice(0, 10) : [];
  if (!student && !requirements.length && !required_courses.length) return null;
  return { student, requirements, required_courses, certifications, ge_shortage };
}

/** 학교에서 읽은 학년·소속·입학 연도로 학생 정보를 채운다. 학교 값이 없는 칸은 그대로 둔다. */
export function fillStudentFromSchool(profile: StudentProfile, school: SchoolStudent | null): StudentProfile {
  if (!school) return profile;
  const next = { ...profile };
  const department = school.department ?? "";
  const inComputing = /컴퓨터학부/.test(department.replace(/\s/g, ""));
  const other = school.other_major ?? "";
  if (inComputing) next.affiliation = "primary";
  else if (/컴퓨터/.test(other)) next.affiliation = /부전공/.test(other) ? "minor" : "double";
  if (school.track) next.majorId = school.track;
  if (school.grade !== null && school.grade <= 4) next.currentGrade = String(school.grade);
  if (school.admission_year) next.admissionYear = school.admission_year;
  if (school.curriculum_year) next.curriculumYear = school.curriculum_year;
  if (!inComputing && department) next.homeDepartment = department.slice(0, 100);
  if (next.affiliation === "primary") {
    if (/편입/.test(school.admission_type ?? "")) next.entryPath = "transfer";
    else if (/신입/.test(school.admission_type ?? "") && !next.entryPath) next.entryPath = "regular";
    if (/복수전공|부전공/.test(other)) {
      next.otherMajor = /복수전공/.test(other) ? "double" : "minor";
      next.otherDepartment = other.replace(/복수전공|부전공/g, "").trim().slice(0, 100);
    }
  }
  return next;
}

export const essentialStateLabel: Record<EssentialCourse["state"], string> = { done: "이수", taking: "수강 중", missing: "미이수", failed: "재이수 필요" };
