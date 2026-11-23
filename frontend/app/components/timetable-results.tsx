"use client";
import { useEffect, useRef, useState } from "react";
import { fetchCandidate, type Candidate, type GenerateTimetableResponse } from "../lib/api";
import { formatMinutes, timeMinutes } from "../lib/planning";
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

function WeekGrid({ candidate }: { candidate: Candidate }) {
  const days = ["월", "화", "수", "목", "금", ...(candidate.sections.some(s => s.meetings.some(m => m.day === "토")) ? ["토"] : [])];
  const blocks = candidate.sections.flatMap((section, index) => section.meetings.map(meeting => ({ section, index, day: meeting.day, start: timeMinutes(meeting.start) ?? 0, end: timeMinutes(meeting.end) ?? 0 }))).filter(b => days.includes(b.day) && b.end > b.start);
  const first = Math.min(9 * 60, ...blocks.map(b => Math.floor(b.start / 60) * 60));
  const last = Math.max(18 * 60, ...blocks.map(b => Math.ceil(b.end / 60) * 60));
  const hours = Array.from({ length: (last - first) / 60 }, (_, i) => first + i * 60);
  const unscheduled = candidate.sections.filter(s => !s.meetings.length);
  return <div className="week-grid-wrap">
    <div className="week-grid" style={{ gridTemplateColumns: `44px repeat(${days.length}, minmax(0, 1fr))`, gridTemplateRows: `26px repeat(${hours.length * 2}, 22px)` }} role="table" aria-label={`${candidate.id} 주간 시간표`}>
      <span className="week-corner" />
      {days.map((day, i) => <span key={day} className="week-day" style={{ gridColumn: i + 2 }} role="columnheader">{day}</span>)}
      {hours.map((hour, i) => <span key={hour} className="week-hour" style={{ gridRow: `${i * 2 + 2} / span 2` }}>{formatMinutes(hour)}</span>)}
      {hours.map((hour, i) => days.map((day, d) => <span key={`${hour}-${day}`} className="week-cell" style={{ gridRow: `${i * 2 + 2} / span 2`, gridColumn: d + 2 }} />))}
      {blocks.map(b => <div key={`${b.section.course_id}-${b.day}-${b.start}`} className="week-block" role="cell"
        style={{ gridColumn: days.indexOf(b.day) + 2, gridRow: `${Math.round((b.start - first) / 30) + 2} / ${Math.round((b.end - first) / 30) + 2}`, background: palette[b.index % palette.length], borderColor: borders[b.index % borders.length] }}
        title={`${b.section.name} (${b.section.course_id}) ${b.day} ${formatMinutes(b.start)}~${formatMinutes(b.end)}`}>
        <strong>{b.section.name}</strong><small>{formatMinutes(b.start)}~{formatMinutes(b.end)}{b.section.room || b.section.building ? ` · ${b.section.building ?? ""} ${b.section.room ?? ""}`.trimEnd() : ""}</small>
      </div>)}
    </div>
    {unscheduled.length > 0 && <p className="week-unscheduled">시간 미정: {unscheduled.map(s => s.name).join(", ")}</p>}
  </div>;
}

function CandidateView({ candidate }: { candidate: Candidate }) {
  return <div className="candidate-view">
    <div className="schedule-summary"><span className="badge">{candidate.id.startsWith("tt_alt") ? "대안" : "자동 생성"}</span><span>{candidate.sections.length}개 분반 · {candidate.total_credits}학점</span><span>공강 {candidate.free_days.length ? candidate.free_days.join("·") : "없음"}</span><span>수업 사이 빈 시간 {Math.round(candidate.gap_minutes / 60 * 10) / 10}시간</span><span>{Object.entries(candidate.credits_by_category).map(([k, v]) => `${k} ${v}`).join(" · ")}</span></div>
    <WeekGrid candidate={candidate} />
    {candidate.warnings.length > 0 && <div className="manual-plan-issues">{candidate.warnings.map(w => <p key={w}>{w}</p>)}</div>}
    <div className="planned-sections">{candidate.sections.map(s => <article key={s.course_id}><div><span>{s.course_id} · {s.credits}학점 · {s.category}{s.area ? ` · ${s.area}` : ""}</span><h3>{s.name}</h3><p>{s.professor || "교수 미정"}{s.grade ? ` · ${s.grade === "*" ? "전학년" : `${s.grade}학년`}` : ""}</p><p>{s.time_raw || "시간 미정"}</p></div></article>)}</div>
  </div>;
}

type Props = { result: GenerateTimetableResponse; stale: boolean; onRegenerate: () => void; generating: boolean; generateError: string | null };

export function TimetableResults({ result, stale, onRegenerate, generating, generateError }: Props) {
  const [tab, setTab] = useState(0);
  const [alternative, setAlternative] = useState<Candidate | null>(null);
  const [loadingAlt, setLoadingAlt] = useState<string | null>(null);
  const [altError, setAltError] = useState<string | null>(null);
  const abort = useRef<AbortController | null>(null);
  // 새 결과가 오면 부모가 key 를 바꿔 이 컴포넌트를 새로 만든다 (탭·대안 초기화).
  useEffect(() => () => abort.current?.abort(), []);
  async function pickAlternative(id: string) {
    abort.current?.abort();
    const controller = new AbortController();
    abort.current = controller;
    setLoadingAlt(id); setAltError(null);
    try {
      const candidate = await fetchCandidate(id, controller.signal);
      setAlternative(candidate); setTab(result.candidates.length);
    } catch (error) {
      if (!controller.signal.aborted) setAltError(error instanceof Error ? error.message : "대안을 불러오지 못했습니다.");
    } finally {
      if (abort.current === controller) setLoadingAlt(null);
    }
  }
  const tabs = [...result.candidates, ...(alternative ? [alternative] : [])];
  const current = tabs[Math.min(tab, tabs.length - 1)];
  const text = statusText[result.status];
  return <div className="timetable-results">
    <div className={`manual-plan-status ${result.status === "success" ? "" : "needs-review"}`} role="status"><strong><span className="badge">{text.badge}</span> {text.title}</strong><p>{text.body} 탐색은 일부 조합만 살펴볼 수 있어 최적해를 보장하지 않습니다.</p></div>
    {stale && <div className="stale-note" role="status"><span>조건이나 이수 과목이 바뀌었어요. 지금 보이는 후보는 이전 조건으로 만든 것입니다.</span><button className="primary-button" disabled={generating} onClick={onRegenerate}>{generating ? <><span className="button-spinner" aria-hidden="true" />만드는 중…</> : "새 조건으로 다시 만들기"}</button></div>}
    {generateError && <div className="planning-errors" role="alert"><p>{generateError}</p></div>}
    {result.warnings.length > 0 && <div className="manual-plan-issues">{result.warnings.map(w => <p key={w}>{w}</p>)}</div>}
    {result.omitted_required.length > 0 && <div className="result-block"><h3>넣지 못한 필수 과목</h3><ul className="omitted-list">{result.omitted_required.map(o => <li key={o.item}><strong>{o.name || o.item}</strong>{o.code && o.code !== o.item ? ` (${o.code})` : ""}<span className="omitted-reason">{reasonText[o.reason] ?? o.reason}</span><p>{o.detail}</p></li>)}</ul></div>}
    {tabs.length > 0 && current && <>
      <div className="option-group candidate-tabs" role="tablist" aria-label="시간표 후보">{tabs.map((c, i) => <button key={c.id} role="tab" aria-selected={c.id === current.id} className={c.id === current.id ? "selected" : ""} onClick={() => setTab(i)}>{c.id.startsWith("tt_alt") ? "선택한 대안" : `${i + 1}안`} · {c.total_credits}학점</button>)}</div>
      <CandidateView key={current.id} candidate={current} />
    </>}
    {result.alternatives.length > 0 && <div className="result-block"><h3>조건을 하나 풀면 이런 안이 있어요</h3><div className="alternative-list">{result.alternatives.map(a => <div className="alternative-card" key={a.id}><div><strong>{a.description}</strong><small>풀어 준 조건: {a.relaxed.join(", ")}</small></div><button className="secondary-button" disabled={loadingAlt !== null} onClick={() => pickAlternative(a.id)}>{loadingAlt === a.id ? "불러오는 중…" : alternative?.id === a.id ? "다시 보기" : "이 대안 보기"}</button></div>)}</div>{altError && <div className="planning-errors" role="alert"><p>{altError}</p></div>}</div>}
    <div className="tip"><Icon name="info" size={17} /><p>후보는 서버 메모리에 잠시 보관됩니다. 서버를 다시 켜면 대안을 불러올 수 없으니 다시 만들어 주세요. 선수과목과 졸업 요건은 아직 검증하지 않습니다.</p></div>
  </div>;
}
