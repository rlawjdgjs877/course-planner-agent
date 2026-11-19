"use client";
/* eslint-disable @next/next/no-img-element -- Live base64 JPEG frames must not go through image optimization. */
import { useCallback, useEffect, useRef, useState, type FormEvent, type KeyboardEvent, type MouseEvent, type ClipboardEvent } from "react";
import { closeKnuSession, knuRequest, KnuApiError, parseKnuFrame, type KnuImportStatus, type KnuInput, type KnuFrame } from "../lib/knu-import";
import type { ImportedCourse } from "../lib/imported-courses";
const remoteKeys = new Set(["Enter", "Backspace", "Tab", "Delete", "Escape", "Home", "End", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "PageUp", "PageDown"]);

export function SchoolImportPanel({ onApply }: { onApply: (courses: ImportedCourse[]) => void }) {
  const [availability, setAvailability] = useState<KnuImportStatus | null>(null);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [running, setRunning] = useState(false);
  const [image, setImage] = useState<string | null>(null);
  const [status, setStatus] = useState("학교 불러오기 서버를 확인하고 있습니다.");
  const [error, setError] = useState("");
  const [result, setResult] = useState<KnuFrame | null>(null);
  const session = useRef<string | null>(null);
  const frameId = useRef<string | null>(null);
  const mounted = useRef(false);
  const screen = useRef<HTMLDivElement>(null);
  const inputQueue = useRef<Promise<unknown>>(Promise.resolve());
  useEffect(() => {
    mounted.current = true;
    const controller = new AbortController();
    void knuRequest<KnuImportStatus>("status", undefined, undefined, controller.signal).then(data => {
      if (!mounted.current || controller.signal.aborted) return;
      setAvailability(data); setStatus(data.available ? "안내를 확인하고 학교 화면을 열어 주세요." : data.reason || "현재 학교 불러오기를 사용할 수 없습니다.");
    }).catch(reason => { if (mounted.current && !controller.signal.aborted) { setStatus("학교 불러오기 연결을 사용할 수 없습니다. 직접 입력으로 진행할 수 있습니다."); setError(reason instanceof Error ? reason.message : "서버 상태를 확인하지 못했습니다."); } });
    const stopOnExit = () => { const token = session.current; session.current = null; if (token) void closeKnuSession(token, true); };
    window.addEventListener("pagehide", stopOnExit);
    return () => { mounted.current = false; controller.abort(); window.removeEventListener("pagehide", stopOnExit); stopOnExit(); };
  }, []);
  const sendInput = useCallback((action: KnuInput) => {
    const token = session.current;
    if (!token) return;
    inputQueue.current = inputQueue.current.then(async () => {
      if (session.current !== token || !mounted.current) return;
      await knuRequest("input", action, token);
    }).catch(reason => { if (mounted.current && session.current === token) setError(reason instanceof Error ? reason.message : "입력을 보내지 못했습니다."); });
  }, []);
  useEffect(() => {
    if (!running) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const controller = new AbortController();
    const poll = async () => {
      const token = session.current;
      if (!token || cancelled) return;
      try {
        const frame = parseKnuFrame(await knuRequest("frame", { have: frameId.current }, token, controller.signal));
        if (cancelled || session.current !== token) return;
        if (frame.image) { setImage(`data:image/jpeg;base64,${frame.image}`); frameId.current = frame.frame_id; }
        setStatus(frame.status);
        if (frame.finished) {
          setResult(frame); setImage(null); session.current = null; setRunning(false);
          const closed = await closeKnuSession(token);
          if (mounted.current) setStatus(closed ? "이수 과목을 읽고 학교 연결을 종료했습니다. 목록을 확인한 뒤 반영해 주세요." : "과목 조회를 마쳤습니다. 연결 종료를 확인하지 못했으며 서버의 만료 시간에 자동 종료됩니다.");
          return;
        }
      } catch (reason) {
        if (cancelled || controller.signal.aborted) return;
        setError(reason instanceof Error ? reason.message : "학교 화면을 읽지 못했습니다.");
        if (reason instanceof KnuApiError && [403, 404, 503].includes(reason.status)) { session.current = null; setRunning(false); setImage(null); void closeKnuSession(token); return; }
      }
      if (!cancelled && session.current === token) timer = setTimeout(poll, document.hidden ? 5000 : 350);
    };
    void poll();
    return () => { cancelled = true; controller.abort(); if (timer) clearTimeout(timer); };
  }, [running]);
  useEffect(() => {
    const node = screen.current;
    if (!running || !node) return;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let delta = 0;
    const wheel = (event: WheelEvent) => { event.preventDefault(); delta += event.deltaY; if (!timer) timer = setTimeout(() => { sendInput({ type: "scroll", delta: Math.max(-2000, Math.min(2000, delta)) }); delta = 0; timer = undefined; }, 120); };
    node.addEventListener("wheel", wheel, { passive: false });
    return () => { node.removeEventListener("wheel", wheel); if (timer) clearTimeout(timer); };
  }, [running, sendInput]);
  async function start() {
    if (!consent || busy || !availability?.available) return;
    setBusy(true); setError(""); setResult(null); setStatus("학교 화면을 열고 있습니다.");
    try {
      const data = await knuRequest<{ session: string }>("start", { consent: true });
      if (typeof data.session !== "string" || !data.session) throw new KnuApiError("학교 연결 정보를 받지 못했습니다.");
      if (!mounted.current) { void closeKnuSession(data.session); return; }
      session.current = data.session; frameId.current = null; setRunning(true);
    } catch (reason) { if (mounted.current) setError(reason instanceof Error ? reason.message : "학교 화면을 열지 못했습니다."); }
    finally { if (mounted.current) setBusy(false); }
  }
  async function stop() {
    const token = session.current; session.current = null; setRunning(false); setImage(null); frameId.current = null; setError("");
    const closed = token ? await closeKnuSession(token) : true;
    if (mounted.current) setStatus(closed ? "학교 연결을 종료했습니다." : "연결 종료를 확인하지 못했습니다. 서버에서 일정 시간 후 자동 종료됩니다.");
  }
  function click(event: MouseEvent<HTMLDivElement>) {
    if (!image) return;
    event.currentTarget.focus(); const rect = event.currentTarget.getBoundingClientRect();
    sendInput({ type: "click", x: Math.max(0, Math.min(1280, (event.clientX - rect.left) / rect.width * 1280)), y: Math.max(0, Math.min(800, (event.clientY - rect.top) / rect.height * 800)) });
  }
  function key(event: KeyboardEvent<HTMLDivElement>) {
    if (event.nativeEvent.isComposing || event.ctrlKey || event.metaKey || event.altKey) return;
    if (event.key.length === 1) { event.preventDefault(); sendInput({ type: "text", text: event.key }); }
    else if (remoteKeys.has(event.key)) { event.preventDefault(); sendInput({ type: "key", key: event.key === "Tab" && event.shiftKey ? "Shift+Tab" : event.key }); }
  }
  function paste(event: ClipboardEvent<HTMLDivElement>) {
    event.preventDefault(); const text = event.clipboardData.getData("text");
    if (text.length > 200) { setError("한 번에 200자 이내로 입력해 주세요."); return; }
    if (text) sendInput({ type: "text", text });
  }
  function sendText(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const field = event.currentTarget.elements.namedItem("remote-text") as HTMLInputElement;
    const text = field.value; field.value = ""; if (text) sendInput({ type: "text", text }); screen.current?.focus();
  }
  async function retryNavigation() {
    const token = session.current; if (!token) return; setError("");
    try { await knuRequest("navigate", {}, token); setStatus("이수성적 조회 메뉴로 이동을 다시 시도합니다."); } catch (reason) { if (mounted.current) setError(reason instanceof Error ? reason.message : "이동을 요청하지 못했습니다."); }
  }
  return <section className="school-import-panel" aria-labelledby="school-import-title"><div className="document-heading"><div><span className="step-label">KNU · SCHOOL IMPORT</span><h2 id="school-import-title">학교 로그인으로 이수 과목 불러오기</h2></div><span className="document-badge">실험 기능</span></div><div className="school-import-notice"><p>Plann 안에서 서버가 제공하는 학교 화면에 직접 로그인합니다. 입력 내용과 학교 세션은 백엔드를 거칩니다. Plann은 아이디·비밀번호·로그인 화면·연결 토큰을 브라우저 저장소에 보관하지 않습니다.</p><p>현재 가져오는 정보는 과목코드·과목명·학점·이수구분입니다. 학년·전공·학적 변동은 자동 확인되지 않습니다. F·NP 제외 외의 재이수·취소와 이수 학기는 직접 확인해 주세요.</p><label><input type="checkbox" checked={consent} disabled={running || busy} onChange={e => setConsent(e.target.checked)} />안내를 확인했으며 본인 계정으로 사용합니다. 확인 후 반영한 과목은 이 브라우저에 저장됩니다.</label></div><p className="school-import-status" role="status">{status}</p>{error && <p className="school-import-error" role="alert">{error}</p>}<div className="school-import-controls">{!running && <button className="primary-button" disabled={!consent || !availability?.available || busy} onClick={start}>{busy ? "학교 화면 여는 중…" : "학교 로그인 화면 열기"}</button>}{running && <><button className="secondary-button" onClick={retryNavigation}>이수성적 조회로 다시 이동</button><button className="secondary-button" onClick={stop}>연결 종료</button></>}</div>{running && <><p className="document-description">아래 학교 화면에서 입력칸을 클릭한 뒤 키보드로 입력하세요. 한글이나 붙여넣기는 입력 보조칸으로 보낼 수 있습니다. {availability?.idle_minutes ?? 10}분간 미사용 시 서버에서 연결을 종료합니다.</p><div className="knu-remote-screen" ref={screen} role="application" tabIndex={0} aria-label="사용자가 직접 조작하는 학교 로그인 화면" onClick={click} onKeyDown={key} onPaste={paste}>{image ? <img src={image} alt="학교 시스템 원격 화면" draggable={false} /> : <span>학교 화면을 불러오는 중입니다…</span>}</div><form className="remote-text-form" onSubmit={sendText}><label htmlFor="remote-school-text">학교 화면의 선택한 입력칸으로 글자 보내기</label><div><input id="remote-school-text" name="remote-text" type="password" autoComplete="off" maxLength={200} placeholder="입력 내용은 전송 후 즉시 지워집니다" /><button className="secondary-button" type="submit">전송 후 지우기</button></div></form></>}{result && <div className="school-import-result"><h3>읽어 온 이수 과목 {result.courses.length}개</h3><p>반영 전 목록을 확인해 주세요. 2026-2 수강 중인 과목 등 제외할 항목이 있으면 반영 후 체크를 해제할 수 있습니다.</p>{result.duplicates.length > 0 && <p className="school-import-warning">같은 코드가 여러 번 조회되어 하나만 남겼습니다. 재이수 내역을 확인해 주세요: {result.duplicates.join(", ")}</p>}<div className="imported-courses-table">{result.courses.map(course => <div key={course.code}><span>{course.code}</span><strong>{course.name}</strong><span>{course.credits ?? "미기재"}학점</span></div>)}</div><button className="primary-button" disabled={!result.courses.length} onClick={() => { onApply(result.courses); setResult(null); setStatus("확인한 이수 과목을 반영했습니다."); }}>확인한 이수 과목 반영</button></div>}</section>;
}

