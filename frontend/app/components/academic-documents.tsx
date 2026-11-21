"use client";
import { useState } from "react";
import { courses } from "../lib/courses";
import { graduationProfiles, platformCohorts, globalCohorts, globalTracks } from "../lib/graduation";
import { prerequisiteChains, startupCourses } from "../lib/prerequisites";
import { Icon } from "./icons";
import { type StudentProfile } from "../lib/student-profile";

export function AcademicDocuments({ selected, toggle, student, onMajorChange, importedNames = [] }: { selected: string[]; toggle: (id: string) => void; student: StudentProfile; onMajorChange: (id: string) => void; importedNames?: string[] }) {
  const [tab, setTab] = useState("graduation");
  const profileId = student.majorId;
  const setProfileId = onMajorChange;
  const primary = student.affiliation === "primary";
  const [cohortId, setCohortId] = useState("");
  const [trackId, setTrackId] = useState("");
  const [category, setCategory] = useState("전체");
  const profile = graduationProfiles.find(p => p.id === profileId);
  const platform = platformCohorts.find(c => c.id === cohortId);
  const global = globalCohorts.find(c => c.id === cohortId);
  const track = globalTracks.find(t => t.id === trackId);
  const categories = ["전체", ...new Set(prerequisiteChains.map(c => c.category))];
  // 이번 학기에 안 열려도 학교에서 불러온 이수 내역에 같은 과목명이 있으면 이수로 본다.
  const imported = new Set(importedNames.map(n => n.replace(/\s+/g, "")));
  const checked = (name: string) => imported.has(name.replace(/\s+/g, "")) || courses.some(c => c.name === name && selected.includes(c.id));
  return <section className="academic-documents" aria-label="첨부 문서 학업 안내">
    <div className="document-heading"><div><span className="step-label">KNU · ACADEMIC GUIDE</span><h2>경북대학교 컴퓨터학부</h2></div><span className="document-badge">첨부 PDF 기준</span></div>
    <div className="document-tabs" role="group" aria-label="학업 안내 선택"><button aria-pressed={tab === "graduation"} onClick={() => setTab("graduation")}><Icon name="book" size={16} />졸업요건</button><button aria-pressed={tab === "prerequisites"} onClick={() => setTab("prerequisites")}><Icon name="list" size={16} />선후수 과목</button></div>
    {tab === "graduation" ? <>
      <p className="document-description">정리 PDF에 기재된 확인일: 2026.11.16 · 본인의 전공을 선택해 주세요.</p>
      <label className="document-field">{primary ? "소속 전공 · 위 학생 정보와 연결" : "주전공 기준을 참고할 전공"}<select value={profileId} onChange={e => { setProfileId(e.target.value); setCohortId(""); setTrackId(""); }}><option value="">전공 선택</option>{graduationProfiles.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
      {profile ? <div className="profile-content">{!primary && <div className="cohort-note"><strong>아래 내용은 컴학 주전공 졸업요건 참고자료입니다.</strong><p>컴학 복수·부전공의 별도 이수요건이나 방문 교환학생 수강 기준으로 적용하지 않습니다. 학생 구분은 화면 위에서 설정할 수 있습니다.</p></div>}<div className="profile-summary"><div><h3>{profile.name}</h3><p>{profile.basis}</p></div><div><strong>{profile.id === "platform" && !platform ? "140~150" : platform && profile.id === "platform" ? platform.total : profile.total}</strong><span>{primary ? "문서의 주전공 졸업학점" : "주전공 기준 · 참고용"}</span></div></div>
        {profile.id === "platform" && <><label className="document-field">입학 학번 구간<select value={cohortId} onChange={e => setCohortId(e.target.value)}><option value="">학번 구간 선택</option>{platformCohorts.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label>{platform ? <div className="cohort-note"><strong>{platform.value}</strong><p>{platform.practice}</p></div> : <p className="document-description">학번을 선택하면 학점 구성과 현장실습 요건이 표시됩니다. 2010학번 이전 기준은 이 자료에 없습니다.</p>}</>}
        {profile.id === "global" && <><div className="document-fields"><label className="document-field">입학 학년도 구간<select value={cohortId} onChange={e => setCohortId(e.target.value)}><option value="">학년도 구간 선택</option>{globalCohorts.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label><label className="document-field">이수 트랙<select value={trackId} onChange={e => setTrackId(e.target.value)}><option value="">트랙 선택</option>{globalTracks.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}</select></label></div>{global && <div className="cohort-note">{global.value}</div>}{track && <div className="cohort-note"><strong>{track.name}</strong><p>{track.value}</p></div>}</>}
        {profile.required.length > 0 && <div className="required-courses"><h4>{primary ? "문서에 명시된 전공필수" : "주전공 전공필수 · 참고용"} <span>{profile.required.filter(checked).length} / {profile.required.length}개 체크</span></h4><div>{profile.required.map(name => { const course = courses.find(c => c.name === name); return <label key={name}><input type="checkbox" checked={checked(name)} disabled={!course} onChange={() => course && toggle(course.id)} /><span>{name}</span></label>; })}</div><p>이수 체크와 학교에서 불러온 내역 중 같은 과목명을 반영합니다. 대체 과목 인정과 최종 졸업 충족 여부는 별도 확인이 필요합니다.</p></div>}
        <dl className="requirements-table">{profile.rows.map(row => <div key={row.label}><dt>{row.label}</dt><dd>{row.value}</dd></div>)}</dl>
        <details className="document-notes"><summary>대체 인정 및 세부 유의사항</summary><ul>{profile.notes.map(note => <li key={note}>{note}</li>)}</ul></details>
        <div className="source-links"><a href={`/documents/graduation-requirements.pdf#page=${profile.sourcePage}`} target="_blank" rel="noreferrer">졸업요건 PDF · {profile.sourcePage}쪽 ↗</a><a href={profile.sourceUrl} target="_blank" rel="noreferrer">PDF에 기재된 학부 안내 ↗</a></div>
      </div> : <div className="document-placeholder"><Icon name="book" size={24} /><p>위에서 학생 정보와 전공을 선택하면 관련 전공의 주전공 졸업요건 자료를 볼 수 있어요.</p><div className="profile-preview">{graduationProfiles.map(p => <button key={p.id} onClick={() => setProfileId(p.id)}>{p.name}<Icon name="arrow" size={13} /></button>)}</div></div>}
      <div className="tip"><Icon name="info" size={17} /><p>첨부 PDF의 참고용 정리를 옮겼습니다. 2026학년도 전공 3개와 2025학년도까지로 표시된 전공 2개를 구분합니다. 입학 학년도·개인 학적·대체 인정에 따른 최종 기준은 학부에 확인하세요. 교양·비교과·전체 이수학점이 없어 졸업 가능 여부를 자동 판정하지 않습니다.</p></div>
    </> : <>
      <p className="document-description">화살표 순서는 PDF의 표기를 옮긴 것입니다. ‘/’ 표기는 원문 그대로이며 선택·동시이수 조건을 임의로 해석하지 않았습니다.</p>
      <label className="document-field">과목 흐름 분류<select value={category} onChange={e => setCategory(e.target.value)}>{categories.map(c => <option key={c}>{c}</option>)}</select></label>
      <div className="prerequisite-list">{prerequisiteChains.filter(c => category === "전체" || c.category === category).map((chain, i) => <article className="prerequisite-chain" key={`${chain.category}-${chain.stages.join()}`}><header><strong>{chain.category}</strong><a href={`/documents/prerequisites.pdf#page=${chain.page}`} target="_blank" rel="noreferrer">원문 {chain.page}쪽 ↗</a></header><ol>{chain.stages.map((stage, j) => <li key={`${i}-${j}`}><span className="chain-stage">{stage.split(" / ").map((name, k) => <span key={name}>{k > 0 && <span className="chain-or"> / </span>}<span className={checked(name) ? "chain-completed" : ""}>{checked(name) && "✓ "}{name}</span></span>)}</span>{j < chain.stages.length - 1 && <span className="chain-arrow" aria-label="다음">→</span>}</li>)}</ol></article>)}</div>
      {(category === "전체") && <article className="startup-list"><h3>글로벌SW · 글솦 창업 교과목</h3><p>원문 2쪽에 나열된 과목이며, 선후수 순서를 뜻하지 않습니다.</p><div>{startupCourses.map(name => <span key={name} className={checked(name) ? "chain-completed" : ""}>{checked(name) && "✓ "}{name}</span>)}</div></article>}
      <div className="tip"><Icon name="info" size={17} /><p>초록색은 이수 체크한 과목입니다. 문서에는 적용 학번과 필수 선이수·권장 순서의 구분이 명시되지 않아 수강 제한으로 자동 적용하지 않습니다. 기초프로그래밍/프로그래밍기초, 데이타통신/데이터통신 등 명칭 차이는 임의로 동일 과목 처리하지 않았습니다.</p></div>
      <div className="source-links"><a href="/documents/prerequisites.pdf" target="_blank" rel="noreferrer">선후수 과목 PDF 전체 보기 ↗</a></div>
    </>}
  </section>;
}
