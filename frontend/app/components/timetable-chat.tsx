"use client";
import { useEffect, useRef, useState } from "react";
import { chatTimetable, type AgentStep, type Alternative, type ChatTurn, type GenerateTimetableRequest, type PlanChatResponse } from "../lib/api";
import { Icon } from "./icons";

type Props = {
  request: GenerateTimetableRequest; candidateId: string | null; run: number;
  /** 화면 후보 탭 id (순서대로). "2안 보여줘"를 서버가 알아듣게 함께 보낸다. */ candidateIds?: string[];
  onApply: (answer: PlanChatResponse) => number; // 새 결과의 run 번호를 돌려준다
  /** 지금 결과가 조건을 다 못 지켰을 때 보여 줄 대안. */
  alternatives?: Alternative[]; status?: "success" | "partial" | "infeasible";
  onPickAlternative?: (id: string) => void; onSelectCandidate?: (id: string) => void;
};
type Turn = ChatTurn & { steps?: AgentStep[]; mode?: "ai" | "rules"; offers?: Alternative[] };

// 기다리는 동안 보여 주는 단계 이름. 실제 결과가 아니라 진행 상태 표시일 뿐이다.
const editStages = ["말 이해", "과목 확인", "시간표 다시 짜기", "검증"];
const explainStages = ["후보 읽기", "조건·근거 확인", "설명 쓰기"];

function ModeBadge({ mode }: { mode?: "ai" | "rules" }) {
  if (!mode) return null;
  return <span className={`agent-mode ${mode}`}>{mode === "ai" ? "AI 에이전트" : "규칙 모드 — OPENAI 키 없음"}</span>;
}

function StepTimeline({ steps, mode, open }: { steps: AgentStep[]; mode?: "ai" | "rules"; open: boolean }) {
  // 가장 최근 답만 펼치고, 이전 답의 단계는 한 줄로 접어 대화가 길어지지 않게 한다.
  const ok = steps.filter(step => step.ok).length;
  return <details className="agent-steps" aria-label="에이전트 작업 과정" open={open}>
    <summary className="agent-steps-head"><span>에이전트가 한 일 · {steps.length}단계{ok === steps.length ? " 완료" : ` 중 ${ok}개 완료`}</span><ModeBadge mode={mode} /></summary>
    <ol>{steps.map((step, i) => <li key={i} className={step.ok ? "ok" : "fail"}>
      <span className="agent-step-icon" aria-hidden="true">{step.ok ? <Icon name="check" size={12} /> : "!"}</span>
      <div><strong>{step.label} <code title="호출한 도구">{step.tool}</code></strong>{step.detail && <small>{step.detail}</small>}</div>
    </li>)}</ol>
  </details>;
}

function PendingTimeline({ stages, title }: { stages: string[]; title: string }) {
  const [at, setAt] = useState(0);
  useEffect(() => {
    const timer = window.setInterval(() => setAt(i => Math.min(i + 1, stages.length - 1)), 900);
    return () => window.clearInterval(timer);
  }, [stages.length]);
  return <div className="chat-bubble assistant pending" role="status">
    <div className="agent-steps"><div className="agent-steps-head"><span>{title}</span></div>
      <ol>{stages.map((stage, i) => <li key={stage} className={i < at ? "passed" : i === at ? "running" : "waiting"}>
        <span className="agent-step-icon" aria-hidden="true">{i === at ? <span className="button-spinner" /> : i < at ? "·" : ""}</span>
        <div><strong>{stage}</strong></div>
      </li>)}</ol>
    </div>
  </div>;
}

export function TimetableChat({ request, candidateId, candidateIds = [], run, onApply, alternatives = [], status = "success", onPickAlternative, onSelectCandidate }: Props) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [folded, setFolded] = useState(false);
  const [explainedRun, setExplainedRun] = useState(0);
  const [ownRun, setOwnRun] = useState(0); // 챗봇이 바꾼 결과는 다시 설명하지 않는다 (답에 이미 설명이 있다)
  const log = useRef<HTMLDivElement>(null);
  const latest = useRef({ request, candidateId, candidateIds, alternatives, status });
  useEffect(() => { latest.current = { request, candidateId, candidateIds, alternatives, status }; });

  useEffect(() => {
    if (!candidateId || run === ownRun) return;
    const controller = new AbortController();
    chatTimetable({ message: null, request: latest.current.request, candidate_id: candidateId, candidate_ids: latest.current.candidateIds, history: [] }, controller.signal)
      .then(answer => {
        const { alternatives: alts, status: st } = latest.current;
        const offers = st !== "success" ? alts.slice(0, 2) : [];
        setTurns(prev => [...prev, { role: "assistant", content: answer.reply, steps: answer.steps, mode: answer.mode }, ...(offers.length ? [{ role: "assistant" as const, content: `${offers.map(a => `‘${a.relaxed.join(", ")}’`).join(" 또는 ")} 조건을 풀면 이런 안이 있어. 볼래?`, offers }] : [])]);
      })
      .catch(error => { if (!controller.signal.aborted) setTurns(prev => [...prev, { role: "assistant", content: error instanceof Error ? error.message : "설명을 불러오지 못했어." }]); })
      .finally(() => { if (!controller.signal.aborted) setExplainedRun(run); });
    return () => controller.abort();
  }, [run, candidateId, ownRun]);
  const explaining = !!candidateId && run !== ownRun && run !== explainedRun;
  // 기다리는 동안은 맨 아래(진행 표시)를, 답이 오면 새 답의 시작(에이전트 작업 과정)을 보여 준다.
  const seen = useRef(0);
  useEffect(() => {
    const box = log.current;
    if (!box) return;
    const items = box.querySelectorAll<HTMLElement>(".chat-turn");
    const first = items[Math.min(seen.current, items.length - 1)];
    const answered = !busy && !explaining && turns.length > seen.current && turns[turns.length - 1]?.role === "assistant";
    if (answered && first) box.scrollTo({ top: first.offsetTop - 4 });
    else box.scrollTo({ top: box.scrollHeight });
    if (!busy && !explaining) seen.current = turns.length;
  }, [turns, busy, explaining]);

  const lastStepTurn = turns.reduce((last, turn, i) => (turn.steps?.length ? i : last), -1);
  const input = useRef<HTMLTextAreaElement>(null);
  // 입력창은 글이 길어지면 6줄까지 늘어나고, 그보다 길면 입력창 안에서 스크롤한다.
  useEffect(() => {
    const box = input.current;
    if (!box) return;
    box.style.height = "auto";
    box.style.height = `${Math.min(box.scrollHeight, 6 * 22 + 20)}px`;
  }, [text]);

  async function send() {
    const message = text.trim();
    if (!message || busy) return;
    const history: ChatTurn[] = turns.filter(t => !t.offers).slice(-8).map(({ role, content }) => ({ role, content }));
    setTurns(prev => [...prev, { role: "user", content: message }]); setText(""); setBusy(true);
    try {
      const answer = await chatTimetable({ message, request: latest.current.request, candidate_id: latest.current.candidateId, candidate_ids: latest.current.candidateIds, history });
      if (answer.applied && answer.response) setOwnRun(onApply(answer));
      else if (answer.select_candidate) onSelectCandidate?.(answer.select_candidate);
      setTurns(prev => [...prev, { role: "assistant", content: answer.reply, steps: answer.steps, mode: answer.mode }]);
    } catch (error) {
      setTurns(prev => [...prev, { role: "assistant", content: error instanceof Error ? error.message : "답을 받지 못했어." }]);
    } finally { setBusy(false); }
  }

  return <section className={`timetable-chat ${folded ? "is-folded" : ""}`} aria-label="시간표 챗봇">
    <div className="document-heading"><div><span className="step-label">PLANN · AI AGENT</span><h2>시간표 도우미</h2><p className="chat-role">조합·검증은 코드가, 해석·설명은 AI 에이전트가 해요.</p></div><button type="button" className="chat-fold" aria-expanded={!folded} onClick={() => setFolded(!folded)}>{folded ? "펼치기" : "접기"}</button></div>
    <div className="chat-log" ref={log} aria-live="polite">
      {!turns.length && !explaining && <p className="chat-empty">1안을 보고 왜 이렇게 짰는지 설명해 줄게. 말하면 1안을 바로 고쳐.</p>}
      {turns.map((turn, i) => <div key={i} className={`chat-turn ${turn.role}`}>
        {turn.role === "assistant" && turn.steps && turn.steps.length > 0 && <StepTimeline key={`${i}-${i === lastStepTurn}`} steps={turn.steps} mode={turn.mode} open={i === lastStepTurn} />}
        {turn.role === "assistant" && (!turn.steps || !turn.steps.length) && turn.mode && <ModeBadge mode={turn.mode} />}
        <div className={`chat-bubble ${turn.role}`}>{turn.content}
          {turn.offers && <div className="chat-offers">{turn.offers.map(a => <button key={a.id} type="button" className="secondary-button" onClick={() => onPickAlternative?.(a.id)}>{a.description} 보기</button>)}</div>}
        </div>
      </div>)}
      {explaining && <PendingTimeline key={`explain-${run}`} title="에이전트가 후보를 읽는 중" stages={explainStages} />}
      {busy && <PendingTimeline key={`edit-${turns.length}`} title="에이전트가 일하는 중" stages={editStages} />}
    </div>
    <form className="chat-input" onSubmit={e => { e.preventDefault(); send(); }}>
      <textarea ref={input} rows={1} aria-label="챗봇에게 말하기" maxLength={500} placeholder="예: 금요일 비워줘, 아침 수업 싫어, ○○ 빼줘" value={text} onChange={e => setText(e.target.value)} disabled={!candidateId}
        onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); send(); } }} />
      <div className="chat-input-foot"><small>Shift+Enter 줄바꿈 · {text.length}/500</small>
        <button className="primary-button" disabled={busy || !text.trim() || !candidateId}>보내기<Icon name="arrow" size={15} /></button></div>
    </form>
  </section>;
}
