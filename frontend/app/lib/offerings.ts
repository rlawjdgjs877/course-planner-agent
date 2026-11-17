import offeringData from "./data/offerings.json";
import sourcesData from "./data/sources.json";
import reportData from "./data/import-report.json";
import type { Course } from "./courses";

export type CourseListing = {
  sourceId: string; crseNo: string; sbjetCd: string; sbjetNm: string; sbjetDvnno: string;
  estblYear: string; estblSmstrSctnm: string; estblGrade: string; estblUnivNm: string;
  estblDprtnNm: string; sbjetSctnm: string; crdit: string; thryTime: string; prctsTime: string;
  totalPrfssNm: string; lssnsTimeInfo: string; lssnsRealTimeInfo: string; lctrmInfo: string;
  rmnmCd: string; rmrk: string; appcrCnt: number | null; attlcPrscpCnt: number | null; pckgeRqstCnt: number | null;
};
export type CourseOffering = { id: string; records: CourseListing[] };
export const courseOfferings = offeringData as CourseOffering[];
export const courseSources = sourcesData;
export const courseImportReport = reportData;
const normalize = (name: string) => name.replace(/\s+/g, "");
const byCode = new Map<string, CourseListing[]>();
const byName = new Map<string, CourseListing[]>();
for (const offering of courseOfferings) for (const record of offering.records) {
  byCode.set(record.sbjetCd, [...(byCode.get(record.sbjetCd) ?? []), record]);
  const key = normalize(record.sbjetNm);
  byName.set(key, [...(byName.get(key) ?? []), record]);
}
export function courseListings(course: Course, sourceId = "all") {
  const records = (course.code ? byCode.get(course.code) : byName.get(normalize(course.name))) ?? [];
  return sourceId === "all" ? records : records.filter(r => r.sourceId === sourceId);
}
export function courseMatchesSource(course: Course, sourceId: string) {
  return sourceId === "all" || courseListings(course, sourceId).length > 0;
}
export function courseMatchesYear(course: Course, year: number, sourceId: string) {
  const records = courseListings(course, sourceId);
  const grades = new Set(records.map(r => r.estblGrade));
  return year === 0 ? !records.length || grades.has("*") || [...grades].every(g => !["1", "2", "3", "4"].includes(g)) : grades.has(String(year));
}
export function courseGradeLabel(course: Course, sourceId = "all") {
  const grades = [...new Set(courseListings(course, sourceId).map(r => r.estblGrade))].filter(Boolean).sort();
  return grades.length ? grades.map(g => g === "*" ? "전학년" : `${g}학년`).join(" / ") : "학년 미확인";
}
export function getCourseOffering(name: string) {
  return byName.get(normalize(name))?.[0];
}
export function offeringDays(record: CourseListing): string[] {
  return [...new Set([...record.lssnsRealTimeInfo.matchAll(/([월화수목금토일])\s*\d/g)].map(match => match[1]))];
}
