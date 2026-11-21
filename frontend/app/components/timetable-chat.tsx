"use client";
import { useEffect, useRef, useState } from "react";
import { chatTimetable, type ChatTurn, type GenerateTimetableRequest, type PlanChatResponse } from "../lib/api";
import { Icon } from "./icons";

type Props = {
  request: GenerateTimetableRequest; candidateId: string | null; run: number;
  onApply: (answer: PlanChatResponse) => number; // 새 결과의 run 번호를 돌려준다
};

export function TimetableChat({ request, candidateId, run, onApply }: Props) {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [folded, setFolded] = useState(false);
  const ownRun = useRef(0); // 챗봇이 바꾼 결과는 다시 설명하지 않는다 (답에 이미 설명이 있다)
  const log = useRef<HTMLDivElement>(null);
  const latest = useRef({ request, candidateId });
  latest.current = { request, candidateId };

  useEffect(() => {
    if (!candidateId || run === ownRun.current) return;
    const controller = new AbortController();
    chatTimetable({ message: null, request: latest.current.request, candidate_id: candidateId, history: [] }, controller.signal)
      .then(answer => setTurns(prev => [...prev, { role: "assistant", content: answer.reply }]))
      .catch(error => { if (!controller.signal.aborted) setTurns(prev => [...prev, { role: "assistant", content: error instanceof Error ? error.message : "설명을 불러오지 못했어." }]); });
    return () => controller.abort();
  }, [run, candidateId]);
  useEffect(() => { log.current?.scrollTo({ top: log.current.scrollHeight }); }, [turns, busy]);

  async function send() {
    const message = text.trim();
    if (!message || busy) return;
    const history = turns.slice(-8);
    setTurns(prev => [...prev, { role: "user", content: message }]); setText(""); setBusy(true);
    try {
      const answer = await chatTimetable({ message, request: latest.current.request, candidate_id: latest.current.candidateId, history });
      if (answer.applied && answer.response) ownRun.current = onApply(answer);
      setTurns(prev => [...prev, { role: "assistant", content: answer.reply }]);
    } catch (error) {
      setTurns(prev => [...prev, { role: "assistant", content: error instanceof Error ? error.message : "답을 받지 못했어." }]);
    } finally { setBusy(false); }
  }

  return <section className={`timetable-chat ${folded ? "is-folded" : ""}`} aria-label="시간표 챗봇">
    <div className="document-heading"><div><span className="step-label">PLANN · CHAT</span><h2>시간표 도우미</h2></div><button type="button" className="chat-fold" aria-expanded={!folded} onClick={() => setFolded(!folded)}>{folded ? "펼치기" : "접기"}</button></div>
    <div className="chat-log" ref={log} aria-live="polite">
      {!turns.length && <p className="chat-empty">1안을 보고 왜 이렇게 짰는지 설명해 줄게. 말하면 1안을 바로 고쳐.</p>}
      {turns.map((turn, i) => <div key={i} className={`chat-bubble ${turn.role}`}>{turn.content}</div>)}
      {busy && <div className="chat-bubble assistant"><span className="button-spinner" aria-hidden="true" /> 시간표 다시 짜는 중…</div>}
    </div>
    <form className="chat-input" onSubmit={e => { e.preventDefault(); send(); }}>
      <input aria-label="챗봇에게 말하기" maxLength={500} placeholder="예: 금요일 비워줘, 아침 수업 싫어, ○○ 빼줘" value={text} onChange={e => setText(e.target.value)} disabled={!candidateId} />
      <button className="primary-button" disabled={busy || !text.trim() || !candidateId}>보내기<Icon name="arrow" size={15} /></button>
    </form>
  </section>;
}
