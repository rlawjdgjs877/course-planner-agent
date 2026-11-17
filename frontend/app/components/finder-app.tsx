"use client";

import { useEffect, useState } from "react";
import { courses } from "../lib/courses";
import { Folder, Icon } from "./icons";
import { AcademicDocuments } from "./academic-documents";
import { SchedulePreview } from "./schedule-preview";
import { PlanningSettings } from "./planning-settings";
import { defaultPlanning, restorePlanning, type PlanningConstraints } from "../lib/planning";
import { StudentProfileCard } from "./student-profile-card";
import { CourseOfferings } from "./course-offerings";
import { courseMatchesSource, courseMatchesYear, courseGradeLabel, courseSources } from "../lib/offerings";
import { AcademicLinkEntry } from "./academic-link-entry";
import { AcademicInputChoice, type AcademicInputMethod } from "./academic-input-choice";
import { normalizeAcademicLink } from "../lib/academic-link";
import { emptyStudentProfile, restoreStudentProfile, type StudentProfile } from "../lib/student-profile";

const sections = [{ title: "이수 과목 체크", icon: "check" }, { title: "시간표 조건 설정", icon: "sliders" }, { title: "나의 시간표", icon: "calendar" }];

export default function FinderApp() {
  const [section, setSection] = useState(0);
  const [showChoice, setShowChoice] = useState(true);
  const [inputMethod, setInputMethod] = useState<AcademicInputMethod | null>(null);
  const [academicLink, setAcademicLink] = useState("");
  const [student, setStudent] = useState<StudentProfile>(emptyStudentProfile);
  const [year, setYear] = useState<number | null>(null);
  const [sourceFilter, setSourceFilter] = useState("all");
  const [selected, setSelected] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [view, setView] = useState("grid");
  const [planning, setPlanning] = useState<PlanningConstraints>(defaultPlanning);
  const [plannedIds, setPlannedIds] = useState<string[]>([]);
  const [ready, setReady] = useState(false);
  const [saveState, setSaveState] = useState("이 브라우저에 자동 저장됩니다");
  useEffect(() => {
    const restoreTimer = window.setTimeout(() => {
    try {
      const stored = JSON.parse(localStorage.getItem("campus-finder-knu-documents-v2") || "null");
      if (stored) {
        if (stored.inputMethod === "link" || stored.inputMethod === "manual") setInputMethod(stored.inputMethod);
        setStudent(restoreStudentProfile(stored.student));
        setAcademicLink(normalizeAcademicLink(stored.academicLink));
        if (Array.isArray(stored.selected)) setSelected(stored.selected.filter((id: string) => courses.some(c => c.id === id)));
        setPlanning(restorePlanning(stored.planning, stored.credits, stored.freeDay));
        if (Array.isArray(stored.plannedIds)) setPlannedIds([...new Set<string>(stored.plannedIds.filter((id: unknown): id is string => typeof id === "string" && id.length <= 100))].slice(0, 100));
      }
    } catch { setSaveState("저장된 정보를 불러오지 못했습니다"); }
    setReady(true);
    }, 0);
    return () => window.clearTimeout(restoreTimer);
  }, []);
  useEffect(() => {
    if (!ready) return;
    try { localStorage.setItem("campus-finder-knu-documents-v2", JSON.stringify({ selected, planning, plannedIds, student, academicLink, inputMethod })); }
    catch { queueMicrotask(() => setSaveState("브라우저 저장이 제한되어 현재 화면에서만 유지됩니다")); }
  }, [selected, planning, plannedIds, student, academicLink, inputMethod, ready]);
  const toggle = (id: string) => setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  const filtered = courses.filter(c => courseMatchesSource(c, sourceFilter) && (year === null || courseMatchesYear(c, year, sourceFilter)) && `${c.name} ${c.code ?? ""}`.toLowerCase().includes(query.toLowerCase()));
  const completed = courses.filter(c => selected.includes(c.id));
  const knownCredits = completed.reduce((total, course) => total + (course.credits ?? 0), 0);
  const unknownCredits = completed.filter(course => course.credits === null).length;
  const togglePlanned = (id: string) => setPlannedIds(prev => prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]);
  const folders = [1, 2, 3, 4, 0];
  const navigate = (index: number) => { setSection(index); setQuery(""); setYear(null); window.scrollTo({ top: 0, behavior: "auto" }); };
  const startWith = (method: AcademicInputMethod) => { setInputMethod(method); navigate(0); setShowChoice(false); };
  return <div className={`desktop ${showChoice ? "is-welcome" : ""}`}>
    <header className="desktop-bar"><span className="desktop-brand"><Icon name="book" size={17} /> Plann</span><span className="desktop-menu">파일 <span>편집</span> <span>보기</span></span><span className="desktop-right">나의 대학 생활, 차곡차곡.</span></header>

    <div className="finder-window">
      <aside className="sidebar">
        <div className="traffic-lights" aria-hidden="true"><i /><i /><i /></div>
        <div className="sidebar-brand"><span className="app-mark"><Icon name="book" size={23} /></span><div>Plann<small>경북대학교 컴퓨터학부</small></div></div>
        <div className="sidebar-label">{showChoice ? "Plann" : "즐겨찾기"}</div>
        <button className={`nav-item home-nav ${showChoice ? "active" : ""}`} aria-current={showChoice ? "page" : undefined} onClick={() => { navigate(0); setShowChoice(true); }}><Icon name="home" /><span>홈</span></button>
        <nav aria-label="주 메뉴">{sections.map((item, i) => <button key={item.title} disabled={showChoice} onClick={() => navigate(i)} className={`nav-item ${!showChoice && section === i ? "active" : ""}`} aria-current={!showChoice && section === i ? "page" : undefined}><Icon name={item.icon} /><span>{item.title}</span>{i === 0 && <small>{selected.length}</small>}</button>)}</nav>
        {!showChoice && <><div className="sidebar-label academic-label">학년별 과목</div>
        <nav aria-label="학년 선택">{folders.map(n => <button key={n} className={`nav-item year-nav ${section === 0 && year === n ? "year-active" : ""}`} onClick={() => { setSection(0); setYear(n); setQuery(""); }}><span className="mini-folder">▰</span>{n === 0 ? "공통·학년 미지정" : `${n}학년`}<span className="nav-count">{courses.filter(c => courseMatchesSource(c, sourceFilter) && courseMatchesYear(c, n, sourceFilter)).length}</span></button>)}</nav></>}
        <details className="sidebar-help"><summary><Icon name="info" size={18} />사용 가이드</summary><p>학적 링크를 저장하거나 직접 입력으로 시작하세요. 링크 자동 불러오기는 아직 연결되지 않았습니다. 저장한 정보는 입력 방법을 바꿔도 유지됩니다.</p></details>
        <div className="sidebar-bottom"><span className="avatar">S</span><div>나의 워크스페이스<small>차근차근, 나만의 속도로</small></div><span className="online-dot" /></div>
      </aside>
      <div className="window-main">
        <header className="toolbar"><div className="toolbar-location"><button className="icon-button back" aria-label="이전 화면" disabled={showChoice} onClick={() => { if (year !== null) setYear(null); else if (section > 0) navigate(section - 1); else setShowChoice(true); }}><Icon name="arrow" /></button>{showChoice && <Icon name="calendar" size={25} />}<span>{showChoice ? "Plann" : sections[section].title}</span></div><div className="toolbar-tools">{showChoice && <div className="welcome-toolbar"><span aria-hidden="true"><Icon name="grid" size={21} /></span><label className="welcome-search"><Icon name="search" size={18} /><input disabled aria-label="과목 검색은 학적 입력 화면에서 이용할 수 있어요" placeholder="검색" /></label></div>}{!showChoice && section === 0 && <><div className="view-switch"><button aria-label="아이콘 보기" aria-pressed={view === "grid"} className={view === "grid" ? "chosen" : ""} onClick={() => setView("grid")}><Icon name="grid" size={17} /></button><button aria-label="목록 보기" aria-pressed={view === "list"} className={view === "list" ? "chosen" : ""} onClick={() => setView("list")}><Icon name="list" size={18} /></button></div><label className="search"><Icon name="search" size={16} /><input aria-label="과목 검색" placeholder="과목 검색" value={query} onChange={e => setQuery(e.target.value)} /></label></>}</div></header>
        <main className={`content ${showChoice ? "onboarding-content" : ""}`}>
          <div className="breadcrumb"><Icon name="book" size={14} /><span>나의 워크스페이스</span><Icon name="arrow" size={11} /><span>{showChoice ? "학적 정보 입력 방법" : sections[section].title}</span>{!showChoice && year !== null && section === 0 && <><Icon name="arrow" size={11} /><span>{year === 0 ? "공통·학년 미지정" : `${year}학년`}</span></>}</div>
          {showChoice ? <AcademicInputChoice savedLink={academicLink} onSaveLink={setAcademicLink} onLinkContinue={() => startWith("link")} onManual={() => startWith("manual")} disabled={!ready} /> : <>
          <div className="page-heading"><div><div className="step-label">STEP 0{section + 1} <span>/ 나만의 시간표 만들기</span></div><h1>{section === 0 ? "배운 만큼, 체크해 보세요." : section === 1 ? "나의 한 주를 그려 보세요." : "이번 학기, 이렇게 시작해요."}</h1><p>{section === 0 ? "경북대학교 컴퓨터학부 문서의 과목을 체크하고 졸업요건을 확인하세요." : section === 1 ? "원하는 학점과 공강 요일로 나에게 맞는 일주일을 준비해요." : "문서의 미이수 과목과 저장한 희망 조건을 확인하세요."}</p></div><span className="heading-icon"><Icon name={sections[section].icon} size={27} /></span></div>
          {section === 0 && <><div className="chosen-input-method"><span>입력 방법: <strong>{inputMethod === "link" ? "학적 링크 입력" : "직접 입력"}</strong></span><button type="button" onClick={() => { setShowChoice(true); window.scrollTo({ top: 0, behavior: "auto" }); }}>입력 방법 바꾸기</button></div>{inputMethod === "link" ? <AcademicLinkEntry savedLink={academicLink} onSave={setAcademicLink} /> : <StudentProfileCard profile={student} onChange={setStudent} />}</>}
          {section === 0 ? <>
            <CourseOfferings sourceId={sourceFilter} onSourceChange={setSourceFilter} plannedIds={plannedIds} onPlanToggle={togglePlanned} />
            <div className="progress-card"><span className="progress-symbol"><Icon name="check" size={21} /></span><div className="progress-copy"><strong>전공·교양 과목, 차근차근 정리해요</strong><span>PDF와 JSON에 수록된 과목입니다. 분반은 한 과목으로 묶으며 졸업 충족률을 뜻하지 않습니다.</span></div><div className="progress-number"><strong>{selected.length}<span> / {courses.length}</span></strong><small>이수 과목</small></div><div className="progress-track"><div style={{ width: `${selected.length / courses.length * 100}%` }} /></div></div>
            <label className="document-field">이수 체크할 과목 분류<select value={sourceFilter} onChange={e => setSourceFilter(e.target.value)}><option value="all">전체 전공·교양</option>{courseSources.map(source => <option value={source.id} key={source.id}>{source.label}</option>)}</select></label>
            <div className="section-heading"><h2>{query ? "검색 결과" : year !== null ? (year === 0 ? "공통·학년 미지정" : `${year}학년 과목`) : "과목 폴더"}<span>{query || year !== null ? `${filtered.length}개 과목` : "5개 폴더"}</span></h2><span>{year !== null || query ? "체크하여 이수 과목 선택" : "폴더를 클릭해 과목을 확인하세요"}</span></div>
            {year === null && !query ? <div className={`folder-grid ${view === "list" ? "folder-list" : ""}`}>{folders.map(n => { const count = completed.filter(c => courseMatchesSource(c, sourceFilter) && courseMatchesYear(c, n, sourceFilter)).length; return <button className="folder-card" key={n} onClick={() => setYear(n)}><Folder /><strong>{n === 0 ? "공통·학년 미지정" : `${n}학년`}</strong><span>{courses.filter(c => courseMatchesSource(c, sourceFilter) && courseMatchesYear(c, n, sourceFilter)).length}개 과목 <b>·</b> {n === 0 ? "전학년·미확인" : "2026년 2학기"}</span><small className={count ? "has-completed" : ""}>{count ? `${count}개 이수 완료` : "이수 과목 선택하기"}</small></button>; })}</div> : <div className="course-list">{filtered.length ? <><div className="course-table-heading"><span>과목명</span><span>구분 · 학점</span></div>{filtered.map(c => <label className={`course-row ${selected.includes(c.id) ? "checked" : ""}`} key={c.id}><input type="checkbox" checked={selected.includes(c.id)} onChange={() => toggle(c.id)} /><span className="course-file"><Icon name="book" size={18} /></span><span className="course-name"><strong>{c.name}</strong><small>{courseGradeLabel(c, sourceFilter)} · {c.semester}{c.code && ` · ${c.code}`}</small></span><span className="course-category">{c.category}</span><span className="course-credit">{c.credits === null ? "학점 미기재" : `${c.credits}학점`}</span></label>)}</> : <div className="empty-state"><Icon name="search" size={30} /><p>표시할 과목이 없어요. 조건을 바꾸거나 공통·학년 미지정 폴더를 확인해 주세요.</p><button onClick={() => setQuery("")}>검색어 지우기</button></div>}</div>}
            <div className="tip"><Icon name="info" size={17} /><div><strong>이수 과목부터 정리하면 더 쉬워요.</strong><p>2026년 2학기 수강신청 전 기준으로 이전 학기까지 완료한 과목만 체크해 주세요. 2026-2 수강 중인 과목은 체크하지 않습니다. 전공·교양을 선택하면 해당 자료의 학년을 기준으로 폴더가 나뉩니다. 전공마다 학년이 다른 과목은 여러 폴더에 보이지만 한 번만 이수 처리됩니다. 개설 학점은 이번 학기 조회값이며 과거 학점 인정은 별도 확인이 필요합니다.</p></div></div>
            <AcademicDocuments key={student.majorId} selected={selected} toggle={toggle} student={student} onMajorChange={majorId => setStudent(prev => ({ ...prev, majorId }))} />
          </> : section === 1 ? <PlanningSettings value={planning} onChange={setPlanning} /> : <SchedulePreview selected={selected} planning={planning} plannedIds={plannedIds} onPlanToggle={togglePlanned} />}
          </>}
        </main>
        {!showChoice && <footer className="content-footer"><span><i className="saved-dot" />{saveState}</span>{section < 2 ? <button className="primary-button" onClick={() => navigate(section + 1)}>{section === 0 ? "시간표 조건 설정" : "담은 시간표 확인"}<Icon name="arrow" size={15} /></button> : <button className="primary-button" onClick={() => navigate(1)}>조건 다시 설정<Icon name="sliders" size={16} /></button>}</footer>}
        <div className="status-bar"><span>{showChoice ? "Plann · 시작하기" : section === 0 ? `5개 폴더 · 수록 ${courses.length}개 과목` : "나의 학업 워크스페이스"}</span><span>{showChoice ? "학적 정보 입력 방법 선택" : <>{selected.length}개 체크 · 확인된 {knownCredits}학점{unknownCredits > 0 && ` + 학점 미확인 ${unknownCredits}개`}</>}</span></div>
      </div>
    </div>
    <p className="desktop-caption"><span className="caption-line" />복잡한 대학 생활을, 조금 더 심플하게.<span className="caption-line" /></p>
  </div>;
}







