"use client";
// 경북대 통합정보시스템에서 이수 과목 불러오기 (실험 기능). 백엔드 /import/knu/* 를 쓴다.
// 학생은 서버가 띄운 학교 화면에 직접 로그인하고, 서버는 과목코드·이름·학점·구분만 돌려준다.
import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent, type MouseEvent } from "react";
import { courses } from "../lib/courses";
import { Icon } from "./icons";

const API = `${process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000"}/import/knu`;
const KEYS = new Set(["Enter", "Backspace", "Tab", "Delete", "Escape", "Home", "End", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "PageUp", "PageDown"]);
type Imported = { code: string; name: string; credits: number | null; category: string | null };
type Status = { available: boolean; reason: string | null; idle_minutes: number };
const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
const norm = (s: string) => s.replace(/\s+/g, "").toLowerCase();

async function api(path: string, body: object = {}, token: string | null = null) {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["X-Import-Session"] = token;
  const res = await fetch(`${API}/${path}`, { method: path === "status" ? "GET" : "POST", headers: path === "status" ? undefined : headers, body: path === "status" ? undefined : JSON.stringify(body) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error(typeof data.detail === "string" ? data.detail : `서버 응답 ${res.status}`), { status: res.status });
  return data;
}

/** 불러온 과목을 이 화면의 과목 id 로 바꾼다. 과목코드가 같으면 우선, 없으면 띄어쓰기를 뺀 이름으로 맞춘다. */
export function matchImported(list: Imported[]) {
  const ids = new Set<string>(); const unmatched: string[] = [];
  for (const item of list) {
    const hits = courses.filter(c => c.code && c.code === item.code);
    const found = hits.length ? hits : courses.filter(c => norm(c.name) === norm(item.name));
    if (found.length) found.forEach(c => ids.add(c.id)); else unmatched.push(`${item.name} (${item.code})`);
  }
  return { ids: [...ids], unmatched };
}

export function KnuImport({ onImport }: { onImport: (ids: string[]) => void }) {
  const [status, setStatus] = useState<Status | null>(null);
  const [consent, setConsent] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [image, setImage] = useState<string | null>(null);
  const [result, setResult] = useState<{ courses: Imported[]; duplicates: string[] } | null>(null);
  const [text, setText] = useState("");
  const [showText, setShowText] = useState(false);
  const [unmatched, setUnmatched] = useState<string[]>([]);
  const [loginForm, setLoginForm] = useState(false);
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const captureRef = useRef<HTMLInputElement>(null);
  const tokenRef = useRef<string | null>(null);
  const queue = useRef<Promise<unknown>>(Promise.resolve());
  const wheel = useRef({ sum: 0, timer: 0 });

  useEffect(() => { api("status").then(setStatus).catch(() => setStatus({ available: false, reason: "백엔드 서버(localhost:8000)에 연결하지 못했습니다.", idle_minutes: 10 })); }, []);

  // 연결 중에는 화면을 계속 받아 온다.
  useEffect(() => {
    if (!token) return;
    let alive = true; let have: string | null = null;
    (async () => {
      while (alive) {
        try {
          const f = await api("frame", { have }, token);
          if (!alive) break;
          if (f.image) { have = f.frame_id; setImage(`data:image/jpeg;base64,${f.image}`); }
          setMessage(f.status); setLoginForm(!!f.login_form);
          if (f.finished) setResult({ courses: f.courses, duplicates: f.duplicates });
        } catch (e) {
          const err = e as Error & { status?: number };
          if ([403, 404, 503].includes(err.status ?? 0)) { end(err.message); break; }
          setMessage(err.message);
        }
        await new Promise(r => setTimeout(r, document.hidden ? 1000 : 120));
      }
    })();
    return () => { alive = false; };
  }, [token]);

  // 페이지를 닫거나 컴포넌트가 사라지면 서버의 브라우저를 바로 닫는다.
  useEffect(() => {
    const close = () => { const t = tokenRef.current; if (t) fetch(`${API}/stop`, { method: "POST", keepalive: true, headers: { "Content-Type": "application/json", "X-Import-Session": t }, body: JSON.stringify({ session: t }) }).catch(() => {}); };
    window.addEventListener("pagehide", close);
    return () => { window.removeEventListener("pagehide", close); close(); };
  }, []);

  function end(msg: string) { tokenRef.current = null; setToken(null); setImage(null); setResult(null); setText(""); setPassword(""); setLoginForm(false); setMessage(msg); }
  async function start() {
    setMessage("학교 화면을 여는 중입니다. 몇 초 걸릴 수 있습니다."); setUnmatched([]);
    try { const { session } = await api("start", { consent }); tokenRef.current = session; setToken(session); }
    catch (e) { setMessage((e as Error).message); }
  }
  async function stop(msg = "연결을 종료했습니다. 브라우저와 읽은 내용을 지웠습니다.") {
    const t = tokenRef.current; end(msg);
    if (t) await api("stop", { session: t }, t).catch(() => {});
  }
  function send(action: object) {
    queue.current = queue.current.then(() => tokenRef.current && api("input", action, tokenRef.current)).catch(e => setMessage((e as Error).message));
  }
  function apply() {
    if (!result) return;
    const { ids, unmatched } = matchImported(result.courses);
    onImport(ids); setUnmatched(unmatched);
    stop(`이수 과목 ${result.courses.length}개 중 ${result.courses.length - unmatched.length}개를 체크하고 연결을 종료했습니다.`);
  }
  async function login(e: FormEvent) {
    e.preventDefault();
    const body = { user_id: userId, password };
    setPassword(""); // 보낸 뒤 바로 지운다
    try { await api("login", body, tokenRef.current); setMessage("로그인하는 중입니다. 로그인하면 이수성적 조회까지 자동으로 이동합니다."); }
    catch (err) { setMessage((err as Error).message); }
  }
  // 숨은 입력칸에 쌓인 글자(영문·숫자, 조합이 끝난 한글)를 보낸다.
  function flushCapture() {
    const el = captureRef.current; if (!el || !el.value) return;
    send({ type: "text", text: el.value.slice(0, 200) }); el.value = "";
  }
  function click(e: MouseEvent<HTMLDivElement>) {
    captureRef.current?.focus({ preventScroll: true });
    const box = e.currentTarget.getBoundingClientRect();
    send({ type: "click", x: clamp(Math.round((e.clientX - box.left) * 1280 / box.width), 0, 1280), y: clamp(Math.round((e.clientY - box.top) * 800 / box.height), 0, 800) });
  }
  function key(e: KeyboardEvent<HTMLInputElement>) {
    if (e.nativeEvent.isComposing || e.key === "Process" || e.ctrlKey || e.metaKey || e.altKey) return; // 글자는 onInput·onCompositionEnd 가 보낸다
    if (KEYS.has(e.key)) { e.preventDefault(); flushCapture(); send({ type: "key", key: e.key === "Tab" && e.shiftKey ? "Shift+Tab" : e.key }); }
  }
  function sendText() { if (text) { send({ type: "text", text: text.slice(0, 200) }); setText(""); } }

  // React 의 onWheel 은 passive 라 preventDefault 가 안 되어 직접 붙인다.
  const screenRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = screenRef.current; if (!el) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault(); wheel.current.sum += e.deltaY;
      if (wheel.current.timer) return;
      wheel.current.timer = window.setTimeout(() => { send({ type: "scroll", delta: clamp(wheel.current.sum, -2000, 2000) }); wheel.current = { sum: 0, timer: 0 }; }, 120);
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, [token]);

  return <section className="academic-link-entry knu-import" aria-labelledby="knu-import-title">
    <div className="document-heading"><div><span className="step-label">IMPORT · 실험 기능</span><h2 id="knu-import-title">경북대 통합정보시스템에서 불러오기</h2></div><span className="link-entry-icon"><Icon name="link" size={35} /></span></div>
    <p className="document-description">학교 화면에 직접 로그인하면 이수성적 조회까지 자동으로 이동해 이수 과목을 체크해 줘요. F·NP 과목은 빠집니다.</p>
    {!status ? <p className="link-entry-idle">불러오기 기능을 확인하는 중…</p> : !status.available ? <p className="link-entry-error">{status.reason}</p> : <>
      {!token && <div className="knu-notice"><ul>
        <li>학교의 공식 연동이 아닙니다. 이 컴퓨터의 서버가 띄운 브라우저가 학교 화면을 열고 자동으로 조작합니다.</li>
        <li>아래 화면에 입력하는 아이디·비밀번호와 로그인 세션은 그 브라우저를 거칩니다. 비밀번호·쿠키·성적은 저장하거나 기록하지 않고, 과목코드·과목명·학점·이수구분만 읽습니다.</li>
        <li>연결 종료를 누르거나, {status.idle_minutes}분 동안 쓰지 않거나, 이 페이지를 닫으면 브라우저와 읽은 내용이 지워집니다.</li>
        <li>보안 검증을 거치지 않은 실험 기능입니다. 본인 계정으로만 쓰고, 꺼려지면 아래에서 직접 체크해 주세요.</li>
      </ul><label className="knu-consent"><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)} /> 위 내용을 이해했고, 본인 계정으로만 사용합니다</label>
      <button type="button" className="primary-button" disabled={!consent} onClick={start}>학교 화면 열기<Icon name="arrow" size={15} /></button></div>}
      {token && <>
        <div className="knu-controls"><button type="button" onClick={() => api("navigate", {}, token).then(() => setMessage("자동 이동을 다시 시도합니다.")).catch(e => setMessage(e.message))}>자동 이동 다시 시도</button><button type="button" onClick={() => stop()}>연결 종료</button></div>
        {loginForm && <form className="knu-login" onSubmit={login}><input value={userId} onChange={e => setUserId(e.target.value)} maxLength={100} autoComplete="username" aria-label="학교 아이디" placeholder="학교 아이디" /><input type="password" value={password} onChange={e => setPassword(e.target.value)} maxLength={200} autoComplete="current-password" aria-label="비밀번호" placeholder="비밀번호" /><button type="submit" className="primary-button" disabled={!userId || !password}>로그인</button></form>}
        <div ref={screenRef} className="knu-screen" onClick={click}>
          {image ? <img src={image} alt="" draggable={false} /> : <span>학교 화면을 불러오는 중입니다</span>}
          <input ref={captureRef} className="knu-capture" aria-label="원격 학교 화면 키보드 입력. 화면을 누른 뒤 그대로 치면 학교 화면에 입력됩니다." autoComplete="off" onKeyDown={key} onInput={e => { if (!(e.nativeEvent as InputEvent).isComposing) flushCapture(); }} onCompositionEnd={flushCapture} onPaste={e => { const t = e.clipboardData.getData("text").slice(0, 200); e.preventDefault(); if (t) send({ type: "text", text: t }); }} />
        </div>
        <p className="link-entry-help">학교 화면의 입력칸을 누르고 그대로 키보드로 치면 돼요(한글 포함). 추가 인증이 나오면 화면을 직접 눌러 진행하세요.</p>
        <details className="knu-fallback"><summary>직접 입력(예비)</summary><div className="knu-typing"><input type={showText ? "text" : "password"} value={text} maxLength={200} autoComplete="off" aria-label="학교 화면에 입력할 글자" placeholder="입력이 잘 안 되면 여기에 적고 보내기" onChange={e => setText(e.target.value)} onKeyDown={e => { if (e.key === "Enter") { e.preventDefault(); sendText(); } }} /><button type="button" aria-pressed={showText} onClick={() => setShowText(v => !v)}>{showText ? "가리기" : "보이기"}</button><button type="button" onClick={sendText}>보내기</button></div></details>
      </>}
      {message && <p className="knu-status" aria-live="polite">{message}</p>}
      {result && <div className="knu-result"><strong>읽은 이수 과목 {result.courses.length}개</strong>
        <ul>{result.courses.map(c => <li key={c.code}>{c.name} <small>{c.code}{c.credits != null && ` · ${c.credits}학점`}{c.category && ` · ${c.category}`}</small></li>)}</ul>
        {result.duplicates.length > 0 && <p className="link-entry-help">같은 과목코드가 여러 번 나와 하나만 남겼습니다: {result.duplicates.join(", ")}. 재이수일 수 있으니 확인해 주세요.</p>}
        <button type="button" className="primary-button" onClick={apply}>이수 과목으로 체크하기<Icon name="check" size={15} /></button></div>}
      {unmatched.length > 0 && <p className="link-entry-help">이 화면 과목 목록에 없어 체크하지 못한 과목: {unmatched.join(", ")}</p>}
    </>}
  </section>;
}
