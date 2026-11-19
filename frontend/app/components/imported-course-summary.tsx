import type { ImportedCourse } from "../lib/imported-courses";
export function ImportedCourseSummary({ courses, matchedCodes, onRemove }: { courses: ImportedCourse[]; matchedCodes: Set<string>; onRemove: (code: string) => void }) {
  if (!courses.length) return null;
  const total = courses.reduce((sum, course) => sum + (course.credits ?? 0), 0);
  const unknown = courses.filter(course => course.credits === null).length;
  const extra = courses.filter(course => !matchedCodes.has(course.code)).length;
  return <section className="imported-history-summary" aria-label="학교에서 불러온 이수 내역"><div className="document-heading"><h2>학교에서 불러온 이수 내역</h2><span className="document-badge">{courses.length}개 · 확인된 {total}학점</span></div><p>과목코드가 일치하는 과목은 이수 체크에 연결했습니다. 현재 개설 목록에 없는 {extra}개도 아래에 보존합니다.{unknown > 0 && ` 학점 미확인 ${unknown}개는 합계에서 제외했습니다.`} 재이수·취소·2026-2 수강 중인 항목이 포함됐는지 직접 확인해 주세요.</p><details><summary>불러온 과목 확인·제외</summary><div className="imported-courses-table">{courses.map(course => <div key={course.code}><span>{course.code}</span><strong>{course.name}<small>{course.category || "이수구분 미기재"}{!matchedCodes.has(course.code) && " · 개설 목록 외 과목"}</small></strong><span>{course.credits ?? "미확인"}학점</span><button onClick={() => onRemove(course.code)}>이수 내역에서 제외</button></div>)}</div></details></section>;
}
