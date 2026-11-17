"use client";

import { useEffect, useState } from "react";
import { courses } from "../lib/courses";
import { Folder, Icon } from "./icons";
import { AcademicDocuments } from "./academic-documents";
import { SchedulePreview } from "./schedule-preview";
import { StudentProfileCard } from "./student-profile-card";
import { AcademicLinkEntry } from "./academic-link-entry";
import { normalizeAcademicLink } from "../lib/academic-link";
import { emptyStudentProfile, restoreStudentProfile, type StudentProfile } from "../lib/student-profile";

const sections = [{ title: "이수 과목 체크", icon: "check" }, { title: "시간표 조건 설정", icon: "sliders" }, { title: "나의 시간표", icon: "calendar" }];

export default function FinderApp() {
  const [section, setSection] = useState(0);
  const [academicLink, setAcademicLink] = useState("");
  const [student, setStudent] = useState<StudentProfile>(emptyStudentProfile);
  const [year, setYear] = useState<number | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [view, setView] = useState("grid");
  const [credits, setCredits] = useState(18);
  const [freeDay, setFreeDay] = useState("금");
  const [ready, setReady] = useState(false);
  const [saveState, setSaveState] = useState("이 브라우저에 자동 저장됩니다");
  useEffect(() => {
    const restoreTimer = window.setTimeout(() => {
    try {
      const stored = JSON.parse(localStorage.getItem("campus-finder-knu-documents-v2") || "null");
      if (stored) {
        setStudent(restoreStudentProfile(stored.student));
        setAcademicLink(normalizeAcademicLink(stored.academicLink));
        if (Array.isArray(stored.selected)) setSelected(stored.selected.filter((id: string) => courses.some(c => c.id === id)));
        if ([12, 15, 18, 21].includes(stored.credits)) setCredits(stored.credits);
        if (["없음", "월", "화", "수", "목", "금"].includes(stored.freeDay)) setFreeDay(stored.freeDay);
      }
    } catch { setSaveState("저장된 정보를 불러오지 못했습니다"); }
    setReady(true);
    }, 0);
    return () => window.clearTimeout(restoreTimer);
  }, []);
  useEffect(() => {
    if (!ready) return;
    try { localStorage.setItem("campus-finder-knu-documents-v2", JSON.stringify({ selected, credits, freeDay, student, academicLink })); }
    catch { queueMicrotask(() => setSaveState("브라우저 저장이 제한되어 현재 화면에서만 유지됩니다")); }
  }, [selected, credits, freeDay, student, academicLink, ready]);
  const toggle = (id: string) => setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  const filtered = courses.filter(c => (year === null || c.year === year) && c.name.toLowerCase().includes(query.toLowerCase()));
  const completed = courses.filter(c => selected.includes(c.id));
  const days = ["월", "화", "수", "목", "금"];
  const folders = [1, 2, 3, 4, 0];
  const navigate = (index: number) => { setSection(index); setQuery(""); setYear(null); };
  return <div className="desktop">
    <header className="desktop-bar"><span className="desktop-brand"><Icon name="book" size={17} /> Campus Finder</span><span className="desktop-menu">파일 <span>편집</span> <span>보기</span></span><span className="desktop-right">나의 대학 생활, 차곡차곡.</span></header>
    <div className="desktop-intro"><span className="eyebrow">A LITTLE MORE ORGANIZED</span><p>대학 생활을 정리하는 가장 편안한 공간.</p></div>
    <div className="finder-window">
      <aside className="sidebar">
        <div className="traffic-lights" aria-hidden="true"><i /><i /><i /></div>
        <div className="sidebar-brand"><span className="app-mark"><Icon name="book" size={23} /></span><div>Campus Finder<small>경북대학교 컴퓨터학부</small></div></div>
        <div className="sidebar-label">즐겨찾기</div>
        <nav aria-label="주 메뉴">{sections.map((item, i) => <button key={item.title} onClick={() => navigate(i)} className={`nav-item ${section === i ? "active" : ""}`} aria-current={section === i ? "page" : undefined}><Icon name={item.icon} /><span>{item.title}</span>{i === 0 && <small>{selected.length}</small>}</button>)}</nav>
        <div className="sidebar-label academic-label">학년별 과목</div>
        <nav aria-label="학년 선택">{folders.map(n => <button key={n} className={`nav-item year-nav ${section === 0 && year === n ? "year-active" : ""}`} onClick={() => { setSection(0); setYear(n); setQuery(""); }}><span className="mini-folder">▰</span>{n === 0 ? "문서 수록 과목" : `${n}학년`}<span className="nav-count">{courses.filter(c => c.year === n).length}</span></button>)}</nav>
        <div className="sidebar-bottom"><span className="avatar">S</span><div>나의 워크스페이스<small>차근차근, 나만의 속도로</small></div><span className="online-dot" /></div>
      </aside>
      <div className="window-main">
        <header className="toolbar"><div className="toolbar-location"><button className="icon-button back" aria-label="이전 화면" disabled={section === 0 && year === null} onClick={() => year !== null ? setYear(null) : navigate(section - 1)}><Icon name="arrow" /></button><span>{sections[section].title}</span></div><div className="toolbar-tools">{section === 0 && <><div className="view-switch"><button aria-label="아이콘 보기" aria-pressed={view === "grid"} className={view === "grid" ? "chosen" : ""} onClick={() => setView("grid")}><Icon name="grid" size={17} /></button><button aria-label="목록 보기" aria-pressed={view === "list"} className={view === "list" ? "chosen" : ""} onClick={() => setView("list")}><Icon name="list" size={18} /></button></div><label className="search"><Icon name="search" size={16} /><input aria-label="과목 검색" placeholder="과목 검색" value={query} onChange={e => setQuery(e.target.value)} /></label></>}</div></header>
        <main className="content">
          <div className="breadcrumb"><Icon name="book" size={14} /><span>나의 워크스페이스</span><Icon name="arrow" size={11} /><span>{sections[section].title}</span>{year !== null && section === 0 && <><Icon name="arrow" size={11} /><span>{year === 0 ? "문서 수록 과목" : `${year}학년`}</span></>}</div>
          <div className="page-heading"><div><div className="step-label">STEP 0{section + 1} <span>/ 나만의 시간표 만들기</span></div><h1>{section === 0 ? "배운 만큼, 체크해 보세요." : section === 1 ? "나의 한 주를 그려 보세요." : "이번 학기, 이렇게 시작해요."}</h1><p>{section === 0 ? "경북대학교 컴퓨터학부 문서의 과목을 체크하고 졸업요건을 확인하세요." : section === 1 ? "원하는 학점과 공강 요일로 나에게 맞는 일주일을 준비해요." : "문서의 미이수 과목과 저장한 희망 조건을 확인하세요."}</p></div><span className="heading-icon"><Icon name={sections[section].icon} size={27} /></span></div>
          {section === 0 && <><AcademicLinkEntry savedLink={academicLink} onSave={setAcademicLink} /><details className="manual-profile"><summary><span>직접 입력</span><small>링크 없이 학생 정보 설정 · 선택 사항</small></summary><StudentProfileCard profile={student} onChange={setStudent} /></details></>}
          {section === 0 ? <>
            <div className="progress-card"><span className="progress-symbol"><Icon name="check" size={21} /></span><div className="progress-copy"><strong>첨부 문서 속 과목, 차근차근 정리해요</strong><span>문서에 등장하는 과목 수이며, 전체 교육과정이나 졸업 충족률이 아닙니다.</span></div><div className="progress-number"><strong>{selected.length}<span> / {courses.length}</span></strong><small>이수 과목</small></div><div className="progress-track"><div style={{ width: `${selected.length / courses.length * 100}%` }} /></div></div>
            <div className="section-heading"><h2>{query ? "검색 결과" : year !== null ? (year === 0 ? "문서 수록 과목" : `${year}학년 과목`) : "과목 폴더"}<span>{query || year !== null ? `${filtered.length}개 과목` : "5개 폴더"}</span></h2><span>{year !== null || query ? "체크하여 이수 과목 선택" : "폴더를 클릭해 과목을 확인하세요"}</span></div>
            {year === null && !query ? <div className={`folder-grid ${view === "list" ? "folder-list" : ""}`}>{folders.map(n => { const count = completed.filter(c => c.year === n).length; return <button className="folder-card" key={n} onClick={() => setYear(n)}><Folder /><strong>{n === 0 ? "문서 수록 과목" : `${n}학년`}</strong><span>{courses.filter(c => c.year === n).length}개 과목 <b>·</b> {n === 0 ? "학년 미기재" : "배정 정보 없음"}</span><small className={count ? "has-completed" : ""}>{count ? `${count}개 이수 완료` : "이수 과목 선택하기"}</small></button>; })}</div> : <div className="course-list">{filtered.length ? <><div className="course-table-heading"><span>과목명</span><span>구분 · 학점</span></div>{filtered.map(c => <label className={`course-row ${selected.includes(c.id) ? "checked" : ""}`} key={c.id}><input type="checkbox" checked={selected.includes(c.id)} onChange={() => toggle(c.id)} /><span className="course-file"><Icon name="book" size={18} /></span><span className="course-name"><strong>{c.name}</strong><small>{c.year === 0 ? "학년 미기재" : `${c.year}학년`} · {c.semester}</small></span><span className="course-category">{c.category}</span><span className="course-credit">{c.credits === null ? "학점 미기재" : `${c.credits}학점`}</span></label>)}</> : <div className="empty-state"><Icon name="search" size={30} /><p>표시할 과목이 없어요. 학년 정보는 PDF에 없어 문서 수록 과목 폴더에 모았습니다.</p><button onClick={() => setQuery("")}>검색어 지우기</button></div>}</div>}
            <div className="tip"><Icon name="info" size={17} /><div><strong>이수 과목부터 정리하면 더 쉬워요.</strong><p>PDF에 학년·학점이 없어 모든 과목을 ‘문서 수록 과목’에 모았습니다. 아래 전공필수 체크와도 연결됩니다.</p></div></div>
            <AcademicDocuments key={student.majorId} selected={selected} toggle={toggle} student={student} onMajorChange={majorId => setStudent(prev => ({ ...prev, majorId }))} />
          </> : section === 1 ? <div className="settings"><div className="setting-card"><span className="setting-number">01</span><h2>이번 학기 희망 학점</h2><p>수강하고 싶은 학점을 선택해 주세요.</p><div className="option-group">{[12, 15, 18, 21].map(n => <button key={n} aria-pressed={credits === n} className={credits === n ? "selected" : ""} onClick={() => setCredits(n)}>{n}학점</button>)}</div></div><div className="setting-card"><span className="setting-number">02</span><h2>비워 두고 싶은 요일</h2><p>나를 위한 하루, 공강 요일을 정해 보세요.</p><div className="option-group">{["없음", ...days].map(d => <button key={d} aria-pressed={freeDay === d} className={freeDay === d ? "selected" : ""} onClick={() => setFreeDay(d)}>{d}{d !== "없음" && "요일"}</button>)}</div></div><div className="tip"><Icon name="info" size={18} /><p>희망 조건을 저장합니다. PDF에는 개별 학점·강의 시간이 없어 현재 이 조건으로 시간표를 자동 배치하지 않습니다.</p></div></div> : <SchedulePreview selected={selected} credits={credits} freeDay={freeDay} />}
        </main>
        <footer className="content-footer"><span><i className="saved-dot" />{saveState}</span>{section < 2 ? <button className="primary-button" onClick={() => navigate(section + 1)}>{section === 0 ? "시간표 조건 설정" : "시간표 준비 현황"}<Icon name="arrow" size={15} /></button> : <button className="primary-button" onClick={() => navigate(1)}>조건 다시 설정<Icon name="sliders" size={16} /></button>}</footer>
        <div className="status-bar"><span>{section === 0 ? `5개 폴더 · 문서 수록 ${courses.length}개 과목` : "나의 학업 워크스페이스"}</span><span>{selected.length}개 과목 체크 · 학점 미기재</span></div>
      </div>
    </div>
    <p className="desktop-caption"><span className="caption-line" />복잡한 대학 생활을, 조금 더 심플하게.<span className="caption-line" /></p>
  </div>;
}



