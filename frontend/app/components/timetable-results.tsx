"use client";
import { useEffect, useImperativeHandle, useRef, useState, type Ref } from "react";
import { fetchCandidate, type ApiSection, type Candidate, type GenerateTimetableResponse, type PrereqIssue } from "../lib/api";
import { formatMinutes, timeMinutes } from "../lib/planning";
import { creditGroup } from "../lib/graduation";
import { Icon } from "./icons";

const statusText = {
  success: { badge: "조건 충족", title: "조건을 모두 지킨 시간표예요", body: "반드시 지킬 조건과 최소 학점을 모두 만족합니다." },
  partial: { badge: "일부 충족", title: "일부 조건을 지키지 못했어요", body: "빠진 필수 과목이나 부족한 학점을 아래에서 확인하고, 대안을 골라 보세요." },
  infeasible: { badge: "후보 없음", title: "조건에 맞는 시간표를 찾지 못했어요", body: "반드시 비울 요일·시간이나 포함할 과목을 줄여 보세요. 아래 대안이 있으면 골라 볼 수 있어요." },
} as const;
const reasonText: Record<string, string> = {
  not_offered: "이번 학기 미개설", already_completed: "이미 이수", excluded: "제외 목록에 있음", not_recommended: "자동 추천 제외",
  free_day_conflict: "공강 요일과 겹침", blocked_time: "비울 시간과 겹침", time_conflict: "다른 필수 과목과 겹침",
};
const palette = ["#e8f3ff", "#fff1e6", "#eaf8ef", "#f3edff", "#fff6d9", "#e9f7f8", "#fdeef3"];
const borders = ["#7fb8f5", "#f2a66b", "#74c495", "#a98be8", "#e6c04d", "#5fbcc3", "#ea8fae"];
const PREREQ_PDF = "/documents/prerequisites.pdf";
const GRADUATION_PDF = "/documents/graduation-requirements.pdf";
const prereqLabel = { missing: "선수 미이수", concurrent: "동시 수강" } as const;

/** 챗봇이 고치기 전 후보와 비교한 결과. 블록 강조와 '빠진 과목' 표시에 쓴다. */
type Diff = { added: Set<string>; removed: ApiSection[] };
function diffCandidates(previous: Candidate, current: Candidate): Diff | null {
  const before = new Set(previous.sections.map(s => s.course_id));
  const now = new Set(current.sections.map(s => s.course_id));
  const added = new Set([...now].filter(id => !before.has(id)));
  const removed = previous.sections.filter(s => !now.has(s.course_id));
  return added.size || removed.length ? { added, removed } : null;
}

export type GraduationInfo = {
  name: string; total: number; done: number; unknown: number; page: number;
  major?: { need: number; done: number | null }; liberal?: { need: number; done: number | null };
};

function WeekGrid({ candidate, diff, issues }: { candidate: Candidate; diff: Diff | null; issues: Map<string, PrereqIssue> }) {
  const sat = candidate.sections.some(s => s.meetings.some(m => m.day === "토")) || !!diff?.removed.some(s => s.meetings.some(m => m.day === "토"));
  const days = ["월", "화", "수", "목", "금", ...(sat ? ["토"] : [])];
  const toBlocks = (sections: ApiSection[]) => sections.flatMap((section, index) => section.meetings.map(meeting => ({ section, index, day: meeting.day, start: timeMinutes(meeting.start) ?? 0, end: timeMinutes(meeting.end) ?? 0 }))).filter(b => days.includes(b.day) && b.end > b.start);
  const blocks = toBlocks(candidate.sections);
  const ghosts = toBlocks(diff?.removed ?? []);
  const all = [...blocks, ...ghosts];
  const first = Math.min(9 * 60, ...all.map(b => Math.floor(b.start / 60) * 60));
  const last = Math.max(18 * 60, ...all.map(b => Math.ceil(b.end / 60) * 60));
  const hours = Array.from({ length: (last - first) / 60 }, (_, i) => first + i * 60);
  const unscheduled = candidate.sections.filter(s => !s.meetings.length);
  const row = (b: { start: number; end: number }) => `${Math.round((b.start - first) / 30) + 2} / ${Math.round((b.end - first) / 30) + 2}`;
  return <div className="week-grid-wrap">
    <div className="week-grid" style={{ gridTemplateColumns: `44px repeat(${days.length}, minmax(0, 1fr))`, gridTemplateRows: `26px repeat(${hours.length * 2}, 22px)` }} role="table" aria-label={`${candidate.id} 주간 시간표`}>
      <span className="week-corner" />
      {days.map((day, i) => <span key={day} className="week-day" style={{ gridColumn: i + 2 }} role="columnheader">{day}</span>)}
      {hours.map((hour, i) => <span key={hour} className="week-hour" style={{ gridRow: `${i * 2 + 2} / span 2` }}>{formatMinutes(hour)}</span>)}
      {hours.map((hour, i) => days.map((day, d) => <span key={`${hour}-${day}`} className="week-cell" style={{ gridRow: `${i * 2 + 2} / span 2`, gridColumn: d + 2 }} />))}
      {ghosts.map(b => <div key={`ghost-${b.section.course_id}-${b.day}-${b.start}`} className="week-block is-ghost" role="cell" style={{ gridColumn: days.indexOf(b.day) + 2, gridRow: row(b) }} title={`빠진 과목: ${b.section.name}`}>
        <strong>{b.section.name}</strong><small>빠짐</small>
      </div>)}
      {blocks.map(b => { const isNew = !!diff?.added.has(b.section.course_id); const issue = issues.get(b.section.course_id); return <div key={`${b.section.course_id}-${b.day}-${b.start}`} className={`week-block ${isNew ? "is-new" : ""} ${issue ? "has-prereq" : ""}`} role="cell"
        style={{ gridColumn: days.indexOf(b.day) + 2, gridRow: row(b), background: palette[b.index % palette.length], borderColor: borders[b.index % borders.length] }}
        title={`${b.section.name} (${b.section.course_id}) ${b.day} ${formatMinutes(b.start)}~${formatMinutes(b.end)}${isNew ? " · 챗봇이 새로 넣음" : ""}${issue ? ` · ${prereqLabel[issue.kind]}` : ""}`}>
        {isNew && <span className="block-tag new">NEW</span>}
        {issue && <span className={`block-tag prereq ${issue.kind}`} aria-label={prereqLabel[issue.kind]}>!</span>}
        <strong>{b.section.name}</strong><small>{formatMinutes(b.start)}~{formatMinutes(b.end)}{b.section.room || b.section.building ? ` · ${b.section.building ?? ""} ${b.section.room ?? ""}`.trimEnd() : ""}</small>
      </div>; })}
    </div>
    {unscheduled.length > 0 && <p className="week-unscheduled">시간 미정: {unscheduled.map(s => s.name).join(", ")}</p>}
  </div>;
}

function GraduationProgress({ candidate, graduation }: { candidate: Candidate; graduation: GraduationInfo }) {
  const add = candidate.total_credits;
  const after = graduation.done + add;
  const pct = (n: number) => `${Math.min(100, n / graduation.total * 100)}%`;
  const byCat = Object.entries(candidate.credits_by_category);
  const addMajor = byCat.filter(([k]) => creditGroup(k) === "major").reduce((s, [, v]) => s + v, 0);
  const addLiberal = byCat.filter(([k]) => creditGroup(k) === "liberal").reduce((s, [, v]) => s + v, 0);
  const part = (label: string, info: { need: number; done: number | null } | undefined, plus: number) => info && <span className="grad-part"><strong>{label}</strong> {info.done === null ? `이번 학기 +${plus}학점 (이수 구분 미확인)` : `${info.done} → ${info.done + plus} / ${info.need}학점`}</span>;
  return <div className="grad-progress" aria-label="졸업 기여도">
    <div className="grad-head"><strong>졸업까지</strong><span>{graduation.name} {graduation.total}학점 중 이수 <b>{graduation.done}</b> → 이번 학기 후 <b>{after}</b>학점 (+{add})</span></div>
    <div className="grad-track" role="img" aria-label={`이수 ${graduation.done}학점, 이번 학기 후 ${after}학점, 졸업 ${graduation.total}학점`}><div className="grad-done" style={{ width: pct(graduation.done) }} /><div className="grad-add" style={{ left: pct(graduation.done), width: `calc(${pct(after)} - ${pct(graduation.done)})` }} /></div>
    <div className="grad-parts">
      {part("전공", graduation.major, addMajor) ?? (addMajor > 0 && <span className="grad-part"><strong>전공</strong> +{addMajor}학점</span>)}
      {part("교양", graduation.liberal, addLiberal) ?? (addLiberal > 0 && <span className="grad-part"><strong>교양</strong> +{addLiberal}학점</span>)}
      <a href={`${GRADUATION_PDF}#page=${graduation.page}`} target="_blank" rel="noreferrer">근거 {graduation.page}쪽</a>
    </div>
    {graduation.unknown > 0 && <small className="grad-note">학점 미확인 이수 과목 {graduation.unknown}개는 뺐습니다. 이수구분별 충족 판정은 학교 시스템에서 확인하세요.</small>}
  </div>;
}

function CandidateView({ candidate, diff, graduation }: { candidate: Candidate; diff: Diff | null; graduation: GraduationInfo | null }) {
  const issueList = candidate.prereq_issues ?? [];
  const issues = new Map(issueList.map(issue => [issue.course_id, issue]));
  // 선수과목 경고는 아래 목록이 근거 쪽 링크와 함께 보여 주므로 같은 문장을 또 띄우지 않는다.
  const warnings = issueList.length ? candidate.warnings.filter(w => !w.startsWith("선수과목 확인")) : candidate.warnings;
  return <div className="candidate-view">
    <div className="schedule-summary"><span className="badge">{candidate.id.startsWith("tt_alt") ? "대안" : "자동 생성"}</span><span>{candidate.sections.length}개 분반 · {candidate.total_credits}학점</span><span>공강 {candidate.free_days.length ? candidate.free_days.join("·") : "없음"}</span><span>수업 사이 빈 시간 {Math.round(candidate.gap_minutes / 60 * 10) / 10}시간</span><span>{Object.entries(candidate.credits_by_category).map(([k, v]) => `${k} ${v}`).join(" · ")}</span></div>
    {diff && <div className="diff-note" role="status"><span className="block-tag new">NEW</span> 챗봇이 바꾼 칸을 표시했어요.{diff.added.size > 0 && <> 새로 들어옴: <strong>{candidate.sections.filter(s => diff.added.has(s.course_id)).map(s => s.name).join(", ")}</strong>.</>}{diff.removed.length > 0 && <> 빠진 과목: <strong>{diff.removed.map(s => s.name).join(", ")}</strong> (점선).</>}</div>}
    {graduation && graduation.total > 0 && <GraduationProgress candidate={candidate} graduation={graduation} />}
    <WeekGrid candidate={candidate} diff={diff} issues={issues} />
    {issueList.length > 0 && <div className="prereq-list" role="note"><strong>선수과목 확인</strong><ul>{issueList.map(issue => <li key={`${issue.course_id}-${issue.kind}`}><span className={`prereq-badge ${issue.kind}`}>{prereqLabel[issue.kind]}</span><span>{issue.name} ← {issue.missing.join(", ")} {issue.kind === "missing" ? "미이수" : "같은 학기 수강"}</span>{issue.page > 0 && <a href={`${PREREQ_PDF}#page=${issue.page}`} target="_blank" rel="noreferrer">근거 {issue.page}쪽</a>}</li>)}</ul></div>}
    {warnings.length > 0 && <div className="manual-plan-issues">{warnings.map(w => <p key={w}>{w}</p>)}</div>}
    <div className="planned-sections">{candidate.sections.map(s => { const issue = issues.get(s.course_id); return <article key={s.course_id} className={diff?.added.has(s.course_id) ? "is-new" : ""}><div><span>{s.course_id} · {s.credits}학점 · {s.category}{s.area ? ` · ${s.area}` : ""}</span><h3>{s.name}{diff?.added.has(s.course_id) && <span className="block-tag new">NEW</span>}{issue && <span className={`prereq-badge ${issue.kind}`}>{prereqLabel[issue.kind]}</span>}</h3><p>{s.professor || "교수 미정"}{s.grade ? ` · ${s.grade === "*" ? "전학년" : `${s.grade}학년`}` : ""}</p><p>{s.time_raw || "시간 미정"}</p></div></article>; })}</div>
  </div>;
}

/** 챗봇 패널이 결과 화면을 움직일 때 쓰는 손잡이. */
export type ResultsHandle = { pickAlternative: (id: string) => void; selectCandidate: (id: string) => void };

type Props = {
  result: GenerateTimetableResponse; stale: boolean; onRegenerate: () => void; generating: boolean; generateError: string | null;
  /** 챗봇이 고치기 전의 후보. 있으면 바뀐 칸을 강조한다. */
  previous?: Candidate | null; initialCandidate?: string | null; graduation?: GraduationInfo | null; ref?: Ref<ResultsHandle>;
};

export function TimetableResults({ result, stale, onRegenerate, generating, generateError, previous = null, initialCandidate = null, graduation = null, ref }: Props) {
  const [tab, setTab] = useState(() => Math.max(0, result.candidates.findIndex(c => c.id === initialCandidate)));
  const [showDiff, setShowDiff] = useState(true);
  const [alternative, setAlternative] = useState<Candidate | null>(null);
  const [loadingAlt, setLoadingAlt] = useState<string | null>(null);
  const [altError, setAltError] = useState<string | null>(null);
  const abort = useRef<AbortController | null>(null);
  const root = useRef<HTMLDivElement>(null);
  // 새 결과가 오면 부모가 key 를 바꿔 이 컴포넌트를 새로 만든다 (탭·대안·강조 초기화).
  useEffect(() => () => abort.current?.abort(), []);
  const chooseTab = (i: number) => { setTab(i); setShowDiff(false); };
  async function pickAlternative(id: string) {
    abort.current?.abort();
    const controller = new AbortController();
    abort.current = controller;
    setLoadingAlt(id); setAltError(null);
    try {
      const candidate = await fetchCandidate(id, controller.signal);
      setAlternative(candidate); chooseTab(result.candidates.length);
      root.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
      if (!controller.signal.aborted) setAltError(error instanceof Error ? error.message : "대안을 불러오지 못했습니다.");
    } finally {
      if (abort.current === controller) setLoadingAlt(null);
    }
  }
  useImperativeHandle(ref, () => ({
    pickAlternative: id => { void pickAlternative(id); },
    selectCandidate: id => { const i = result.candidates.findIndex(c => c.id === id); if (i >= 0) { chooseTab(i); root.current?.scrollIntoView({ behavior: "smooth", block: "start" }); } },
  }));
  const tabs = [...result.candidates, ...(alternative ? [alternative] : [])];
  const current = tabs[Math.min(tab, tabs.length - 1)];
  const diff = showDiff && previous && current && !current.id.startsWith("tt_alt") ? diffCandidates(previous, current) : null;
  const text = statusText[result.status];
  return <div className="timetable-results" ref={root}>
    <div className={`manual-plan-status ${result.status === "success" ? "" : "needs-review"}`} role="status"><strong><span className="badge">{text.badge}</span> {text.title}</strong><p>{text.body} 탐색은 일부 조합만 살펴볼 수 있어 최적해를 보장하지 않습니다.</p></div>
    {stale && <div className="stale-note" role="status"><span>조건이나 이수 과목이 바뀌었어요. 지금 보이는 후보는 이전 조건으로 만든 것입니다.</span><button className="primary-button" disabled={generating} onClick={onRegenerate}>{generating ? <><span className="button-spinner" aria-hidden="true" />만드는 중…</> : "새 조건으로 다시 만들기"}</button></div>}
    {generateError && <div className="planning-errors" role="alert"><p>{generateError}</p></div>}
    {result.warnings.length > 0 && <div className="manual-plan-issues">{result.warnings.map(w => <p key={w}>{w}</p>)}</div>}
    {result.omitted_required.length > 0 && <div className="result-block"><h3>넣지 못한 필수 과목</h3><ul className="omitted-list">{result.omitted_required.map(o => <li key={o.item}><strong>{o.name || o.item}</strong>{o.code && o.code !== o.item ? ` (${o.code})` : ""}<span className="omitted-reason">{reasonText[o.reason] ?? o.reason}</span><p>{o.detail}</p></li>)}</ul></div>}
    {tabs.length > 0 && current && <>
      <div className="option-group candidate-tabs" role="tablist" aria-label="시간표 후보">{tabs.map((c, i) => <button key={c.id} role="tab" aria-selected={c.id === current.id} className={c.id === current.id ? "selected" : ""} onClick={() => chooseTab(i)}>{c.id.startsWith("tt_alt") ? "선택한 대안" : `${i + 1}안`} · {c.total_credits}학점</button>)}</div>
      <CandidateView key={current.id} candidate={current} diff={diff} graduation={graduation} />
    </>}
    {result.alternatives.length > 0 && <div className="result-block"><h3>조건을 하나 풀면 이런 안이 있어요</h3><div className="alternative-list">{result.alternatives.map(a => <div className="alternative-card" key={a.id}><div><strong>{a.description}</strong><small>풀어 준 조건: {a.relaxed.join(", ")}</small></div><button className="secondary-button" disabled={loadingAlt !== null} onClick={() => pickAlternative(a.id)}>{loadingAlt === a.id ? "불러오는 중…" : alternative?.id === a.id ? "다시 보기" : "이 대안 보기"}</button></div>)}</div>{altError && <div className="planning-errors" role="alert"><p>{altError}</p></div>}</div>}
    <div className="tip"><Icon name="info" size={17} /><p>후보는 서버 메모리에 잠시 보관됩니다. 서버를 다시 켜면 대안을 불러올 수 없으니 다시 만들어 주세요. 선수과목은 학부 권장 이수 순서(<a href={PREREQ_PDF} target="_blank" rel="noreferrer">근거 PDF</a>) 기준으로 확인합니다. 최종 수강 가능 여부는 수강신청 시스템에서 확인하세요.</p></div>
  </div>;
}
