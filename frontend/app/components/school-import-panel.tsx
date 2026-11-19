"use client";
// 학교 로그인으로 이수 과목 불러오기. 백엔드 /import/knu/* 를 쓴다.
// 서버가 띄운 브라우저가 학교 로그인 칸을 채우고 이수성적 조회까지 자동으로 가서 과목코드·이름·학점·구분만 돌려준다.
// 학교 화면은 보여 주지 않는다. 학생은 아이디·비밀번호만 넣는다.
import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { closeKnuSession, knuRequest, KnuApiError, parseKnuFrame, type KnuImportStatus, type KnuFrame } from "../lib/knu-import";
import type { ImportedCourse } from "../lib/imported-courses";

const GIVE_UP_MS = 60_000; // 로그인 뒤 이만큼 지나도 과목이 안 오면 실패로 본다
const LOGIN_FAIL_MS = 3_000; // 로그인을 보낸 뒤 이만큼 지나도 로그인 칸이 그대로면 로그인 실패로 본다

/** 서버 상태 문구를 세 단계로 줄인다. */
function stage(message: string) {
  if (/조회 버튼|불러오는 중|응답/.test(message)) return "과목 읽는 중";
  if (/메뉴|조회 화면|자동 이동/.test(message)) return "성적 메뉴 찾는 중";
  return "로그인 중";
}

export function SchoolImportPanel({ onApply, autoStart = false }: { onApply: (courses: ImportedCourse[]) => void; autoStart?: boolean }) {
  const [availability, setAvailability] = useState<KnuImportStatus | null>(null);
  const [consent, setConsent] = useState(autoStart);
  const autoStartPending = useRef(autoStart);
  const starting = useRef(false);
  const [attempted, setAttempted] = useState(false);
  const [busy, setBusy] = useState(autoStart);
  const [running, setRunning] = useState(false);
  const [loginForm, setLoginForm] = useState(false);
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [loginAt, setLoginAt] = useState<number | null>(null);
  const loginAtRef = useRef<number | null>(null);
  const [now, setNow] = useState(0);
  const [status, setStatus] = useState("학교 불러오기 서버를 확인하고 있습니다.");
  const [error, setError] = useState("");
  const [result, setResult] = useState<KnuFrame | null>(null);
  const session = useRef<string | null>(null);
  const mounted = useRef(false);

  const resetLogin = () => { loginAtRef.current = null; setLoginAt(null); setLoginForm(false); setPassword(""); };
  const startSession = useCallback(async () => {
    if (starting.current || session.current) return;
    starting.current = true; setAttempted(true);
    setBusy(true); setError(""); setResult(null); setStatus("학교 로그인 화면을 여는 중입니다.");
    try {
      const data = await knuRequest<{ session: string }>("start", { consent: true });
      if (typeof data.session !== "string" || !data.session) throw new KnuApiError("학교 연결 정보를 받지 못했습니다.");
      if (!mounted.current) { void closeKnuSession(data.session); return; }
      session.current = data.session; setRunning(true);
    } catch (reason) { if (mounted.current) setError(reason instanceof Error ? reason.message : "학교 로그인 화면을 열지 못했습니다."); }
    finally { starting.current = false; if (mounted.current) setBusy(false); }
  }, []);

  useEffect(() => {
    mounted.current = true;
    const controller = new AbortController();
    void knuRequest<KnuImportStatus>("status", undefined, undefined, controller.signal).then(data => {
      if (!mounted.current || controller.signal.aborted) return;
      setAvailability(data);
      if (data.available && autoStartPending.current) {
        autoStartPending.current = false;
        void startSession();
      } else {
        autoStartPending.current = false; setBusy(false);
        setStatus(data.available ? "안내를 확인하고 불러오기를 시작해 주세요." : data.reason || "현재 학교 불러오기를 사용할 수 없습니다.");
      }
    }).catch(reason => { if (mounted.current && !controller.signal.aborted) { autoStartPending.current = false; setBusy(false); setStatus("학교 불러오기 연결을 사용할 수 없습니다. 직접 입력으로 진행할 수 있습니다."); setError(reason instanceof Error ? reason.message : "서버 상태를 확인하지 못했습니다."); } });
    const stopOnExit = () => { const token = session.current; session.current = null; if (token) void closeKnuSession(token, true); };
    window.addEventListener("pagehide", stopOnExit);
    return () => { mounted.current = false; controller.abort(); window.removeEventListener("pagehide", stopOnExit); stopOnExit(); };
  }, [startSession]);

  // 연결 중에는 진행 상태만 받아 온다 (학교 화면 캡처는 받지 않는다).
  useEffect(() => {
    if (!running) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const controller = new AbortController();
    const giveUp = (token: string, message: string) => {
      session.current = null; setRunning(false); resetLogin(); void closeKnuSession(token);
      setError(message); setStatus("학교 연결을 종료했습니다.");
    };
    const poll = async () => {
      const token = session.current;
      if (!token || cancelled) return;
      try {
        const frame = parseKnuFrame(await knuRequest("frame", { image: false }, token, controller.signal));
        if (cancelled || session.current !== token) return;
        const at = loginAtRef.current;
        setStatus(frame.status); setLoginForm(frame.login_form); setNow(Date.now());
        if (frame.finished) {
          setResult(frame); session.current = null; setRunning(false); resetLogin();
          const closed = await closeKnuSession(token);
          if (mounted.current) setStatus(closed ? "이수 과목을 읽고 학교 연결을 종료했습니다. 목록을 확인한 뒤 반영해 주세요." : "과목 조회를 마쳤습니다. 연결 종료를 확인하지 못했으며 서버의 만료 시간에 자동 종료됩니다.");
          return;
        }
        if (at && frame.login_form && Date.now() - at > LOGIN_FAIL_MS) {
          loginAtRef.current = null; setLoginAt(null);
          setError("로그인되지 않았어요. 아이디와 비밀번호를 확인해 주세요.");
        } else if (at && (frame.needs_help || Date.now() - at > GIVE_UP_MS)) {
          giveUp(token, "자동으로 불러오지 못했어요. 학교 성적 메뉴를 찾지 못했습니다. 다시 시도하거나 직접 입력해 주세요.");
          return;
        }
      } catch (reason) {
        if (cancelled || controller.signal.aborted) return;
        if (reason instanceof KnuApiError && [403, 404, 503].includes(reason.status)) { giveUp(token, reason.message); return; }
        setError(reason instanceof Error ? reason.message : "진행 상태를 읽지 못했습니다.");
      }
      if (!cancelled && session.current === token) timer = setTimeout(poll, document.hidden ? 1000 : 300);
    };
    void poll();
    return () => { cancelled = true; controller.abort(); if (timer) clearTimeout(timer); };
  }, [running]);

  async function start() {
    if (!consent || busy || !availability?.available) return;
    await startSession();
  }
  async function stop() {
    const token = session.current; session.current = null; setRunning(false); resetLogin(); setError("");
    const closed = token ? await closeKnuSession(token) : true;
    if (mounted.current) setStatus(closed ? "학교 연결을 종료했습니다." : "연결 종료를 확인하지 못했습니다. 서버에서 일정 시간 후 자동 종료됩니다.");
  }
  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = session.current;
    if (!token || !userId || !password) return;
    const body = { user_id: userId, password };
    setPassword(""); setError(""); // 보낸 뒤 바로 지운다
    try {
      await knuRequest("login", body, token);
      const at = Date.now(); loginAtRef.current = at; setLoginAt(at); setNow(at); setLoginForm(false);
    } catch (reason) { if (mounted.current) setError(reason instanceof Error ? reason.message : "로그인 정보를 보내지 못했습니다."); }
  }

  const waitingForLogin = running && loginForm && loginAt === null;
  const working = (busy || running) && !waitingForLogin;
  const seconds = loginAt !== null ? Math.max(0, Math.round((now - loginAt) / 1000)) : null;
  return <section className="school-import-panel" aria-labelledby="school-import-title"><div className="document-heading"><div><span className="step-label">KNU · SCHOOL IMPORT</span><h2 id="school-import-title">학교 로그인으로 이수 과목 불러오기</h2></div><span className="document-badge">실험 기능</span></div><details className="school-import-notice" open={autoStart ? undefined : true}><summary>학교 로그인·저장 안내</summary><p>통합정보시스템 아이디·비밀번호를 넣으면 연결 서버가 띄운 브라우저가 학교 로그인 칸을 채우고 이수성적 조회까지 자동으로 진행합니다. 학교의 공식 연동은 아닙니다.</p><p>아이디·비밀번호는 학교 로그인 칸에 넣는 데만 쓰고 서버와 브라우저 어디에도 저장하거나 기록하지 않습니다. 과목을 다 읽으면 학교 세션을 담은 브라우저를 바로 닫습니다.</p><p>현재 가져오는 정보는 과목코드·과목명·학점·이수구분입니다. 학년·전공·학적 변동은 자동 확인되지 않습니다. F·NP 제외 외의 재이수·취소와 이수 학기는 직접 확인해 주세요.</p>{!autoStart && <label><input type="checkbox" checked={consent} disabled={running || busy} onChange={e => setConsent(e.target.checked)} />안내를 확인했으며 본인 계정으로 사용합니다. 확인 후 반영한 과목은 이 브라우저에 저장됩니다.</label>}</details>
    {!working && !waitingForLogin && <p className="school-import-status" role="status">{status}</p>}
    {waitingForLogin && <form className="school-login-form" onSubmit={login}><label htmlFor="school-login-id">통합정보시스템 아이디</label><input id="school-login-id" value={userId} onChange={e => setUserId(e.target.value)} maxLength={100} autoComplete="username" placeholder="아이디" /><label htmlFor="school-login-password">비밀번호</label><input id="school-login-password" type="password" value={password} onChange={e => setPassword(e.target.value)} maxLength={200} autoComplete="current-password" placeholder="비밀번호" /><div className="school-import-controls"><button type="submit" className="primary-button" disabled={!userId || !password}>로그인하고 불러오기</button><button type="button" className="secondary-button" onClick={stop}>취소</button></div></form>}
    {working && <div className="school-import-progress" role="status" aria-live="polite"><span className="button-spinner" aria-hidden="true" /><div><strong>{loginAt === null ? "학교 로그인 화면을 여는 중…" : `${stage(status)}…`}</strong>{seconds !== null && <small>{seconds}초</small>}</div>{running && <button type="button" className="secondary-button" onClick={stop}>취소</button>}</div>}
    {error && <p className="school-import-error" role="alert">{error}</p>}
    {!running && !busy && !result && availability?.available && (!autoStart || attempted) && <div className="school-import-controls"><button className="primary-button" disabled={!consent} onClick={start}>{error ? "다시 시도" : "불러오기 시작"}</button></div>}
    {result && <div className="school-import-result"><h3>읽어 온 이수 과목 {result.courses.length}개</h3><p>반영 전 목록을 확인해 주세요. 2026-2 수강 중인 과목 등 제외할 항목이 있으면 반영 후 체크를 해제할 수 있습니다.</p>{result.duplicates.length > 0 && <p className="school-import-warning">같은 코드가 여러 번 조회되어 하나만 남겼습니다. 재이수 내역을 확인해 주세요: {result.duplicates.join(", ")}</p>}<div className="imported-courses-table">{result.courses.map(course => <div key={course.code}><span>{course.code}</span><strong>{course.name}</strong><span>{course.credits ?? "미기재"}학점</span></div>)}</div><button className="primary-button" disabled={!result.courses.length} onClick={() => { onApply(result.courses); setResult(null); setStatus("확인한 이수 과목을 반영했습니다."); }}>확인한 이수 과목 반영</button></div>}
  </section>;
}
