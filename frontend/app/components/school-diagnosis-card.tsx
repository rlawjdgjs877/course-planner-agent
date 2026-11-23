"use client";
// 학교 졸업자가진단에서 읽어 온 학생 정보, 교과구분별 학점, 필수과목. 공식 졸업사정은 학교 화면이 기준이다.
import { essentialStateLabel, type SchoolDiagnosis } from "../lib/school-diagnosis";
import { Icon } from "./icons";

const fmt = (n: number | null) => n === null ? "-" : Number.isInteger(n) ? String(n) : n.toFixed(1);

export function SchoolDiagnosisCard({ diagnosis, geAreas, mustInclude, onAddGe, onAddMust }: {
  diagnosis: SchoolDiagnosis; geAreas: string[]; mustInclude: string[];
  onAddGe: (areas: string[]) => void; onAddMust: (key: string) => void;
}) {
  const s = diagnosis.student;
  const chips = s ? [
    s.grade && `${s.grade}학년`, s.department, s.admission_year && `${s.admission_year} 입학`, s.curriculum_year && `${s.curriculum_year} 교육과정`,
    s.admission_type, s.status, s.semesters !== null && `${s.semesters}학기 이수`, s.other_major && `다전공 ${s.other_major}`,
    s.total_credits !== null && `취득 ${fmt(s.total_credits)}학점`, s.math_exempt && "수리·기초과학 면제", s.teaching && "교직 이수",
  ].filter((x): x is string => typeof x === "string" && !!x) : [];
  const missingGe = diagnosis.ge_shortage.filter(area => !geAreas.includes(area));
  const todo = diagnosis.required_courses.filter(c => c.state === "missing" || c.state === "failed");
  const rows = diagnosis.requirements.filter(r => r.name !== "평점평균");
  return <section className="school-diagnosis" aria-labelledby="school-diagnosis-title">
    <div className="document-heading"><div><span className="step-label">KNU · 졸업자가진단</span><h2 id="school-diagnosis-title">학교에서 확인한 내 졸업 현황</h2></div><span className="document-badge">학교 화면 기준</span></div>
    {chips.length > 0 && <div className="student-summary">{chips.map(chip => <span key={chip}>{chip}</span>)}</div>}
    {diagnosis.ge_shortage.length > 0 && <div className={`diagnosis-callout${missingGe.length ? "" : " is-done"}`}><Icon name="info" size={17} /><div><strong>부족한 교양 영역: {diagnosis.ge_shortage.join(", ")}</strong><p>{missingGe.length ? "시간표를 만들 때 이 영역의 교양을 먼저 넣도록 조건에 추가할 수 있어요." : "시간표 조건의 '우선 채울 교양 영역'에 들어가 있어요."}</p></div>{missingGe.length > 0 && <button type="button" className="secondary-button" onClick={() => onAddGe(missingGe)}>조건에 추가</button>}</div>}
    {rows.length > 0 && <div className="diagnosis-table" role="table" aria-label="교과구분별 취득학점">
      <div role="row" className="diagnosis-row is-head"><span role="columnheader">교과구분</span><span role="columnheader">기준</span><span role="columnheader">이수</span><span role="columnheader">부족</span><span role="columnheader">충족</span></div>
      {rows.map(r => <div role="row" key={`${r.group}-${r.major}-${r.name}`} className={`diagnosis-row${r.satisfied === false ? " is-short" : ""}`}>
        <span role="cell"><strong>{r.name}</strong>{r.group && <small>{r.group}{r.major ? ` · ${r.major}` : ""}</small>}</span>
        <span role="cell">{fmt(r.required)}</span><span role="cell">{fmt(r.earned)}</span>
        <span role="cell">{r.shortage ? fmt(r.shortage) : "-"}</span><span role="cell">{r.satisfied === null ? "-" : r.satisfied ? "충족" : "미충족"}</span>
      </div>)}
    </div>}
    {diagnosis.required_courses.length > 0 && <div className="diagnosis-essential"><h3>필수과목 {diagnosis.required_courses.length - todo.length}/{diagnosis.required_courses.length} 이수</h3><ul>{diagnosis.required_courses.map(c => {
      const key = c.code ?? c.name;
      const added = mustInclude.includes(key);
      return <li key={`${key}-${c.major}`} className={`is-${c.state}`}><span className="essential-state">{essentialStateLabel[c.state]}</span><strong>{c.name}</strong>{c.code && <small>{c.code}</small>}{c.credits !== null && <small>{fmt(c.credits)}학점</small>}{(c.state === "missing" || c.state === "failed") && <button type="button" className="secondary-button" disabled={added} onClick={() => onAddMust(key)}>{added ? "시간표에 넣기로 함" : "이번 시간표에 넣기"}</button>}</li>;
    })}</ul><p>이번 학기에 열리지 않거나 학년이 맞지 않는 과목은 넣지 못할 수 있어요.</p></div>}
    {diagnosis.certifications.length > 0 && <div className="diagnosis-essential"><h3>졸업자격인정</h3><ul>{diagnosis.certifications.map(c => <li key={c.area}><span className="essential-state">{c.passed ? "합격" : c.exempt ? "면제" : "미취득"}</span><strong>{c.area}</strong></li>)}</ul></div>}
    <p className="diagnosis-note">이번 학기 수강 중인 과목은 성적이 나오기 전이라 이수에서 뺐어요. 학교 졸업자가진단 결과를 옮긴 참고 자료예요. 최종 졸업 판정은 학교 통합정보시스템과 학부에서 확인하세요.</p>
  </section>;
}
