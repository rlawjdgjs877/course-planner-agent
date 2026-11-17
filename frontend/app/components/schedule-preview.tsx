"use client";
import { courses } from "../lib/courses";
import { CourseOfferings } from "./course-offerings";
import { courseOfferings } from "../lib/offerings";
import { checkSectionConflicts, formatMinutes, validatePlanning, parseMeetingTimes, type PlanningConstraints } from "../lib/planning";
import { Icon } from "./icons";

export function SchedulePreview({ selected, planning, plannedIds, onPlanToggle }: { selected: string[]; planning: PlanningConstraints; plannedIds: string[]; onPlanToggle: (id: string) => void }) {
  const completed = courses.filter(c => selected.includes(c.id));
  const completedNames = completed.map(c => c.name);
  const resolved = plannedIds.map(id => ({ id, offering: courseOfferings.find(o => o.records[0].crseNo === id) }));
  const missing = resolved.filter(item => !item.offering).map(item => item.id);
  const records = resolved.flatMap(item => item.offering ? [{ ...item.offering.records[0], inconsistent: new Set(item.offering.records.map(r => r.lssnsRealTimeInfo.replace(/\s/g, ""))).size > 1, creditInconsistent: new Set(item.offering.records.map(r => r.crdit)).size > 1 }] : []);
  const report = checkSectionConflicts(records.map(r => ({ id: r.crseNo, code: r.sbjetCd, name: r.sbjetNm, time: r.lssnsRealTimeInfo, inconsistent: r.inconsistent })));
  const creditsUnknown = records.some(r => r.creditInconsistent || !r.crdit || !Number.isFinite(Number(r.crdit)));
  const credits = records.reduce((sum, r) => sum + (r.creditInconsistent ? 0 : Number(r.crdit) || 0), 0);
  const preferenceErrors = validatePlanning(planning);
  const completedInPlan = records.filter(r => completed.some(c => c.code ? c.code === r.sbjetCd : c.name.replace(/\s/g, "") === r.sbjetNm.replace(/\s/g, "")));
  const hardConflicts: string[] = [];
  for (const record of records) {
    const meetings = record.inconsistent ? null : parseMeetingTimes(record.lssnsRealTimeInfo);
    if (!meetings) continue;
    if (meetings.some(m => planning.free_days.includes(m.day as typeof planning.free_days[number]))) hardConflicts.push(`${record.crseNo}: 반드시 비울 요일에 수업이 있습니다.`);
    if (meetings.some(m => planning.blocked_times.some(b => b.day === m.day && m.start < Number(b.end.slice(0, 2)) * 60 + Number(b.end.slice(3)) && Number(b.start.slice(0, 2)) * 60 + Number(b.start.slice(3)) < m.end))) hardConflicts.push(`${record.crseNo}: 반드시 비울 시간과 겹칩니다.`);
    if (planning.exclude.includes(record.crseNo) || planning.exclude.includes(record.sbjetCd)) hardConflicts.push(`${record.crseNo}: 제외한 과목입니다.`);
  }
  const unmetIncludes = planning.must_include.filter(id => !records.some(r => r.crseNo === id || r.sbjetCd === id));
  const hasProblems = !report.ok || missing.length > 0;
  return <section className="schedule-preview"><div className="scope-banner"><Icon name="calendar" size={18} /><div><strong>직접 담은 분반 확인 · 2026년 2학기</strong><p>시간과 분반 중복은 실제 개설 자료로 검사합니다. 선수과목·교육과정 요건·자동 조합 탐색은 아직 연결되지 않았습니다.</p></div></div><div className="schedule-summary"><span className="badge">직접 구성</span><span>{records.length}개 분반 · 확인된 {credits}학점{creditsUnknown ? " + 학점 확인 필요" : ""}</span><span>목표 {planning.target_credits}학점</span></div>
    {!plannedIds.length ? <div className="cohort-note"><strong>아래 강좌 목록에서 ‘시간표에 담기’를 눌러 보세요.</strong><p>같은 과목의 여러 분반을 담으면 중복을 안내하고, 시간이 없는 강좌는 판정 보류로 표시합니다.</p></div> : <>
      <div className={`manual-plan-status ${hasProblems ? "needs-review" : ""}`} role="status"><strong>{hasProblems ? "시간·분반 확인이 필요해요" : "선택한 분반 간 시간 충돌·중복이 없어요"}</strong><p>선수과목은 검증된 규칙 데이터가 없어 모두 ‘확인 필요’입니다. 시간 검사를 통과해도 수강 가능 판정을 뜻하지 않습니다.</p></div>
      <div className="planned-sections">{records.map(record => <article key={record.crseNo}><div><span>{record.crseNo} · {record.crdit || "미기재"}학점</span><h3>{record.sbjetNm}</h3><p>{record.lssnsTimeInfo || "교시 미기재"}</p><p>{record.lssnsRealTimeInfo || "시간 미정 · 판정 보류"}</p><small>선수과목 확인 필요{record.inconsistent ? " · 자료별 수업 시간 불일치" : ""}</small></div><button className="secondary-button" onClick={() => onPlanToggle(record.crseNo)}>빼기</button></article>)}</div>
      <div className="manual-plan-issues" aria-live="polite">{report.conflicts.map((c, i) => <p key={i}>시간 충돌: {c.a} ↔ {c.b} · {c.day} {formatMinutes(c.start)}~{formatMinutes(c.end)}</p>)}{report.duplicate_courses.map(c => <p key={c.code}>동일 과목 분반 중복: {c.sections.join(", ")}</p>)}{report.unresolved.map(id => <p key={id}>시간 미정 또는 자료 불일치 · 판정 보류: {id}</p>)}{missing.map(id => <p key={id}>현재 개설 데이터에서 찾을 수 없음: {id} <button onClick={() => onPlanToggle(id)}>제거</button></p>)}{completedInPlan.map(r => <p key={r.crseNo}>이미 이수 체크한 과목입니다: {r.sbjetNm}</p>)}{hardConflicts.map(message => <p key={message}>{message}</p>)}{unmetIncludes.length > 0 && <p>반드시 포함할 과목 미선택: {unmetIncludes.join(", ")}</p>}{!creditsUnknown && credits > planning.max_credits && <p>최대 학점 {planning.max_credits}학점을 초과했습니다.</p>}{!creditsUnknown && credits < planning.min_credits && <p>{planning.credits_strict ? "필수 최소 학점 미달" : "희망 최소 학점 미달"}: 현재 {credits} / 최소 {planning.min_credits}학점</p>}{preferenceErrors.map(error => <p key={error}>{error}</p>)}</div>
    </>}
    <CourseOfferings excludeNames={completedNames} plannedIds={plannedIds} onPlanToggle={onPlanToggle} /><div className="tip"><Icon name="info" size={17} /><p>자동 추천 후보·대안·최적해 여부는 백엔드 엔진의 실제 응답이 있을 때 표시할 예정입니다. 시간 미정 강좌를 충돌 없음으로 처리하지 않습니다.</p></div></section>;
}
