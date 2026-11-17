"use client";
import { useState } from "react";
import { courseOfferings, courseSources, courseImportReport, offeringDays, type CourseListing } from "../lib/offerings";
import { Icon } from "./icons";

const pageSize = 10;
export function CourseOfferings({ sourceId, onSourceChange, excludeNames = [] }: { sourceId?: string; onSourceChange?: (id: string) => void; excludeNames?: string[] }) {
  const [localSource, setLocalSource] = useState("all");
  const [query, setQuery] = useState("");
  const [grade, setGrade] = useState("all");
  const [day, setDay] = useState("all");
  const [page, setPage] = useState(1);
  const source = sourceId ?? localSource;
  const excluded = new Set(excludeNames.map(name => name.replace(/\s+/g, "")));
  const matching = courseOfferings.flatMap(offering => {
    const records = offering.records.filter(record => (source === "all" || record.sourceId === source) && (grade === "all" || record.estblGrade === grade) && (day === "all" || offeringDays(record).includes(day)) && !excluded.has(record.sbjetNm.replace(/\s+/g, "")) && `${record.sbjetNm} ${record.crseNo} ${record.totalPrfssNm} ${record.estblDprtnNm}`.toLowerCase().includes(query.trim().toLowerCase()));
    return records.length ? [{ ...offering, records }] : [];
  });
  const pages = Math.max(1, Math.ceil(matching.length / pageSize));
  const currentPage = Math.min(page, pages);
  const changeSource = (id: string) => { (onSourceChange ?? setLocalSource)(id); setPage(1); };
  const label = (id: string) => courseSources.find(s => s.id === id)?.label ?? id;
  const gradeLabel = (record: CourseListing) => record.estblGrade === "*" ? "전학년" : record.estblGrade ? `${record.estblGrade}학년` : "학년 미기재";
  return <section className="course-offerings" aria-label="개설 강좌 검색"><div className="document-heading"><div><span className="step-label">KNU · COURSE EXPLORER</span><h2>전공·교양 개설 강좌</h2></div><span className="document-badge">2026 · 2학기</span></div>
    <div className="catalog-stats"><span><strong>{courseImportReport.sourceCount}</strong>개 자료</span><span><strong>{courseImportReport.offeringCount}</strong>개 분반</span><span><strong>{courseImportReport.courseCodes}</strong>개 과목</span></div>
    <p className="document-description">2026.11.16 조회 자료 {courseImportReport.sourceRows}개 항목을 강좌번호별로 묶었습니다. 같은 강좌의 전공별 학년·구분은 따로 보존합니다. 제공된 파일 범위의 목록이며 전체 개설 강좌나 실시간 잔여석을 보장하지 않습니다.</p>
    <div className="offering-filters"><label>전공·교양<select value={source} onChange={e => changeSource(e.target.value)}><option value="all">전체 자료</option>{["전공", "교양"].map(group => <optgroup key={group} label={group}>{courseSources.filter(s => s.group === group).map(s => <option value={s.id} key={s.id}>{s.label} · 원본 {s.count}개</option>)}</optgroup>)}</select></label><label>검색<input aria-label="개설 강좌 검색" placeholder="과목명 · 교수 · 강좌번호" value={query} onChange={e => { setQuery(e.target.value); setPage(1); }} /></label><label>학년<select value={grade} onChange={e => { setGrade(e.target.value); setPage(1); }}><option value="all">전체 학년</option>{["1", "2", "3", "4"].map(n => <option value={n} key={n}>{n}학년</option>)}<option value="*">전학년 표기</option></select></label><label>요일<select value={day} onChange={e => { setDay(e.target.value); setPage(1); }}><option value="all">전체 요일</option>{["월", "화", "수", "목", "금", "토", "일"].map(d => <option key={d}>{d}</option>)}</select></label></div>
    <div className="offering-results" aria-live="polite">검색 결과 {matching.length}개 분반 · {currentPage} / {pages}페이지</div>
    {matching.slice((currentPage - 1) * pageSize, currentPage * pageSize).map(offering => { const record = offering.records[0]; const days = offeringDays(record); return <article key={offering.id} className="offering-card"><header><div><span className="offering-code">{record.crseNo} · {record.estblYear}년 {record.estblSmstrSctnm}</span><h3>{record.sbjetNm}</h3><p>{record.estblUnivNm} · {record.estblDprtnNm}</p></div><strong className="offering-credits">{record.crdit || "—"}<small>학점</small></strong></header><div className="offering-tags"><span>{record.sbjetSctnm || "이수 구분 미기재"}</span><span>{gradeLabel(record)}</span>{days.some(d => d === "토" || d === "일") && <span>주말 수업</span>}{offering.records.map(r => <span key={r.sourceId}>{label(r.sourceId)}</span>)}</div><dl><div><dt>담당 교수</dt><dd>{record.totalPrfssNm || "미기재"}</dd></div><div><dt>수업 시간</dt><dd>{record.lssnsRealTimeInfo ? record.lssnsRealTimeInfo.split(",").map((time, i) => <span className="offering-time" key={i}>{time}</span>) : "수업 시간 미기재 · 자동 시간표 배치 불가"}</dd></div><div><dt>강의실</dt><dd>{[record.lctrmInfo, record.rmnmCd].filter(Boolean).join(" · ") || "미기재"}</dd></div><div><dt>이론 / 실습</dt><dd>{record.thryTime || "미기재"} / {record.prctsTime || "미기재"}</dd></div><div><dt>조회 인원</dt><dd>신청 {record.appcrCnt ?? "미기재"} / 정원 {record.attlcPrscpCnt ?? "미기재"} · 꾸러미 신청 {record.pckgeRqstCnt ?? "미기재"}</dd></div>{record.rmrk && <div><dt>비고</dt><dd>{record.rmrk}</dd></div>}</dl>
      <details><summary>자료별 분류·학년 및 세부 정보 ({offering.records.length}개)</summary>{offering.records.map(r => <div className="offering-source-detail" key={r.sourceId}><strong>{label(r.sourceId)} · {gradeLabel(r)} · {r.sbjetSctnm}</strong><p>{r.estblDprtnNm} · {r.crdit || "미기재"}학점 · 분반 {r.sbjetDvnno}</p><p>{r.totalPrfssNm || "교수 미기재"} / {r.lssnsRealTimeInfo || "시간 미기재"}</p><p>{[r.lctrmInfo, r.rmnmCd].filter(Boolean).join(" · ") || "강의실 미기재"}</p><p>교시: {r.lssnsTimeInfo || "미기재"}</p>{r.rmrk && <p>{r.rmrk}</p>}<p>조회: {courseSources.find(s => s.id === r.sourceId)?.timestamp.replace("T", " ")}</p></div>)}</details></article>; })}
    {!matching.length && <div className="empty-state"><Icon name="search" size={28} /><p>조건에 맞는 강좌가 없어요.</p><button onClick={() => { changeSource("all"); setQuery(""); setGrade("all"); setDay("all"); }}>필터 초기화</button></div>}
    <nav className="offering-pagination" aria-label="개설 강좌 페이지"><button disabled={currentPage === 1} onClick={() => setPage(currentPage - 1)}>이전</button><span>{currentPage} / {pages}</span><button disabled={currentPage === pages} onClick={() => setPage(currentPage + 1)}>다음</button></nav>
    <div className="tip"><Icon name="info" size={17} /><p>이수 구분과 권장 학년은 조회 전공에 따라 다를 수 있습니다. 분반을 확인해 주세요. 원격강좌·영어강의·수강대상 제한은 비고에 표시하며, 파일에 없는 학기나 수강 자격은 추측하지 않습니다.</p></div>
  </section>;
}
