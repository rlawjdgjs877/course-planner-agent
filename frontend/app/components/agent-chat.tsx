"use client";
import { useEffect, useRef, useState } from "react";
import type { AgentStep } from "../lib/api";
import { Icon } from "./icons";

export type AgentChatEntry = {
  id: number; role: "user" | "assistant"; content: string; steps?: AgentStep[];
  applied?: boolean; undone?: boolean; error?: boolean; summary?: boolean;
};

const suggestions = ["금요일 비워줘", "아침 9시 수업은 빼줘", "교양 하나 더 넣어줘", "이 과목들 왜 골랐어?", "알고리즘2 들어도 돼?"];
const toolIcon: Record<string, string> = { search_courses: "search", update_timetable: "calendar", check_prerequisites: "list" };

type Props = {
  entries: AgentChatEntry[]; busy: boolean; busyLabel: string | null; unavailable: string | null;
  onSend: (message: string) => void; onUndo: (id: number) => void; canUndo: (id: number) => boolean;
};

export function AgentChat({ entries, busy, busyLabel, unavailable, onSend, onUndo, canUndo }: Props) {
  const [draft, setDraft] = useState("");
  const log = useRef<HTMLDivElement | null>(null);
  useEffect(() => { log.current?.scrollTo({ top: log.current.scrollHeight, behavior: "smooth" }); }, [entries.length, busy]);
  function submit(text: string) {
    const message = text.trim();
    if (!message || busy) return;
    onSend(message); setDraft("");
  }
  return <aside className="agent-chat" aria-label="시간표 에이전트">
    <header className="agent-chat-header"><span className="agent-chat-mark"><Icon name="book" size={17} /></span><div><strong>Plann 에이전트</strong><small>과목을 찾고, 시간표를 다시 짜고, 선수과목을 확인해요</small></div></header>
    <div className="agent-chat-log" ref={log} aria-live="polite">
      {entries.length === 0 && !busy && <div className="agent-chat-empty"><p>시간표를 만들면 여기서 요약해 드려요. 그다음 말로 고쳐 보세요.</p></div>}
      {entries.map(entry => <div key={entry.id} className={`agent-msg ${entry.role} ${entry.error ? "error" : ""}`}>
        {entry.steps && entry.steps.length > 0 && <ol className="agent-steps">{entry.steps.map((step, i) => <li key={i} className={step.ok ? "" : "failed"}><Icon name={toolIcon[step.tool] ?? "info"} size={13} />{step.label}{!step.ok && " · 적용 안 됨"}</li>)}</ol>}
        <p>{entry.content}</p>
        {entry.applied && <div className="agent-applied"><span>{entry.undone ? "되돌렸어요" : "시간표에 반영했어요"}</span>{!entry.undone && canUndo(entry.id) && <button type="button" onClick={() => onUndo(entry.id)} disabled={busy}>되돌리기</button>}</div>}
      </div>)}
      {busy && <div className="agent-msg assistant pending"><span className="button-spinner" aria-hidden="true" />{busyLabel ?? "생각하는 중…"}</div>}
    </div>
    {unavailable && <p className="agent-chat-unavailable" role="status">{unavailable}</p>}
    <div className="agent-chat-suggestions">{suggestions.map(s => <button type="button" key={s} disabled={busy} onClick={() => submit(s)}>{s}</button>)}</div>
    <form className="agent-chat-input" onSubmit={e => { e.preventDefault(); submit(draft); }}>
      <input aria-label="에이전트에게 말하기" placeholder="예: 운영체제 넣고 목요일은 비워줘" value={draft} maxLength={500} onChange={e => setDraft(e.target.value)} disabled={busy} />
      <button type="submit" className="primary-button" disabled={busy || !draft.trim()} aria-label="보내기"><Icon name="arrow" size={15} /></button>
    </form>
  </aside>;
}
