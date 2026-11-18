"use client";
// 경북대 통합정보시스템에서 이수 과목 불러오기 (실험 기능). 백엔드 /import/knu/* 를 쓴다.
// 서버가 띄운 브라우저가 학교 로그인 칸을 채우고 이수성적 조회까지 자동으로 가서 과목코드·이름·학점·구분만 돌려준다.
// 학교 화면은 보여 주지 않는다. 학생은 아이디·비밀번호만 넣는다.
import { useEffect, useRef, useState, type FormEvent } from "react";
import { courses } from "../lib/courses";
import { Icon } from "./icons";

const API = `${process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000"}/import/knu`;
const GIVE_UP_MS = 60_000; // 로그인 뒤 이만큼 지나도 과목이 안 오면 실패로 본다
type Imported = { code: string; name: string; credits: number | null; category: string | null };
type Status = { available: boolean; reason: string | null; idle_minutes: number };
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

/** 서버 상태 문구를 세 단계로 줄인다. */
function stage(message: string) {
  if (/조회 버튼|불러오는 중/.test(message)) return "과목 읽는 중";
  if (/메뉴|조회 화면|자동 이동/.test(message)) return "성적 메뉴 찾는 중";
  return "로그인 중";
}

export function KnuImport({ onImport }: { onImport: (ids: string[]) => void }) {
  const [status, setStatus] = useState<Status | null>(null);
  const [consent, setConsent] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [result, setResult] = useState<{ courses: Imported[]; duplicates: string[] } | null>(null);
  const [unmatched, setUnmatched] = useState<string[]>([]);
  const [loginForm, setLoginForm] = useState(false);
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [loginAt, setLoginAt] = useState<number | null>(null);
  const [now, setNow] = useState(0);
  const tokenRef = useRef<string | null>(null);
  const loginAtRef = useRef<number | null>(null); // 진행 확인 반복문에서 읽는 로그인 시각

  useEffect(() => { api("status").then(setStatus).catch(() => setStatus({ available: false, reason: "백엔드 서버(localhost:8000)에 연결하지 못했습니다.", idle_minutes: 10 })); }, []);

  // 연결 중에는 진행 상태만 받아 온다 (화면 캡처는 받지 않는다).
  useEffect(() => {
    if (!token) return;
    let alive = true;
    const giveUp = (reason: string) => {
      tokenRef.current = null; loginAtRef.current = null;
      api("stop", { session: token }, token).catch(() => {});
      setToken(null); setLoginForm(false); setLoginAt(null);
      setError(`자동으로 불러오지 못했어요. ${/찾지 못|멈췄/.test(reason) ? "학교 메뉴를 찾지 못했습니다." : reason}`);
    };
    (async () => {
      while (alive) {
        try {
          const f = await api("frame", { image: false }, token);
          if (!alive) break;
          const at = loginAtRef.current;
          setMessage(f.status); setLoginForm(!!f.login_form); setNow(Date.now());
          if (f.finished) { setResult({ courses: f.courses, duplicates: f.duplicates }); break; }
          if (at && f.login_form && Date.now() - at > 3000) { loginAtRef.current = null; setLoginAt(null); setError("로그인되지 않았어요. 아이디와 비밀번호를 확인해 주세요."); }
          else if (at && (/멈췄|찾지 못|읽지 못|열지 못/.test(f.status) || Date.now() - at > GIVE_UP_MS)) { giveUp(f.status); break; }
        } catch (e) {
          const err = e as Error & { status?: number };
          if ([403, 404, 503].includes(err.status ?? 0)) { giveUp(err.message); break; }
        }
        await new Promise(r => setTimeout(r, document.hidden ? 1000 : 300));
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

  async function stop() {
    const t = tokenRef.current;
    tokenRef.current = null; loginAtRef.current = null; setToken(null); setPassword(""); setLoginForm(false); setLoginAt(null);
    if (t) await api("stop", { session: t }, t).catch(() => {});
  }
  async function start() {
    setError(""); setResult(null); setUnmatched([]); setMessage("학교 로그인 화면을 여는 중입니다.");
    try { const { session } = await api("start", { consent }); tokenRef.current = session; setToken(session); }
    catch (e) { setError((e as Error).message); }
  }
  async function login(e: FormEvent) {
    e.preventDefault();
    const body = { user_id: userId, password };
    setPassword(""); setError(""); // 보낸 뒤 바로 지운다
    try { await api("login", body, tokenRef.current); const at = Date.now(); loginAtRef.current = at; setLoginAt(at); setLoginForm(false); setMessage("로그인하는 중입니다."); }
    catch (err) { setError((err as Error).message); }
  }
  function apply() {
    if (!result) return;
    const { ids, unmatched } = matchImported(result.courses);
    onImport(ids); setUnmatched(unmatched); setResult(null); stop();
    setMessage(`이수 과목 ${result.courses.length}개 중 ${result.courses.length - unmatched.length}개를 체크했어요.`);
  }

  const working = token && !result && (loginAt !== null || !loginForm);
  return <section className="academic-link-entry knu-import" aria-labelledby="knu-import-title">
    <div className="document-heading"><div><span className="step-label">IMPORT · 실험 기능</span><h2 id="knu-import-title">경북대 통합정보시스템에서 불러오기</h2></div><span className="link-entry-icon"><Icon name="link" size={35} /></span></div>
    <p className="document-description">통합정보시스템 아이디·비밀번호만 넣으면 이수 과목을 자동으로 읽어서 체크해 줘요. F·NP 과목은 빠집니다.</p>
    {!status ? <p className="link-entry-idle">불러오기 기능을 확인하는 중…</p> : !status.available ? <p className="link-entry-error">{status.reason}</p> : <>
      {!token && !result && <div className="knu-notice"><ul>
        <li>학교의 공식 연동이 아닙니다. 이 컴퓨터의 서버가 띄운 브라우저가 학교 로그인과 이수성적 조회를 대신 진행합니다.</li>
        <li>아이디·비밀번호는 그 브라우저의 학교 로그인 칸에 넣는 데만 쓰고, 비밀번호·쿠키·성적은 저장하거나 기록하지 않습니다. 과목코드·과목명·학점·이수구분만 읽습니다.</li>
        <li>과목을 다 읽거나, {status.idle_minutes}분 동안 쓰지 않거나, 이 페이지를 닫으면 브라우저가 닫힙니다.</li>
        <li>보안 검증을 거치지 않은 실험 기능입니다. 본인 계정으로만 쓰고, 꺼려지면 아래에서 직접 체크해 주세요.</li>
      </ul><label className="knu-consent"><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)} /> 위 내용을 이해했고, 본인 계정으로만 사용합니다</label>
      <button type="button" className="primary-button" disabled={!consent} onClick={start}>{error ? "다시 시도" : "불러오기 시작"}<Icon name="arrow" size={15} /></button></div>}
      {token && loginForm && loginAt === null && !result && <form className="knu-login" onSubmit={login}><input value={userId} onChange={e => setUserId(e.target.value)} maxLength={100} autoComplete="username" aria-label="학교 아이디" placeholder="통합정보시스템 아이디" /><input type="password" value={password} onChange={e => setPassword(e.target.value)} maxLength={200} autoComplete="current-password" aria-label="비밀번호" placeholder="비밀번호" /><button type="submit" className="primary-button" disabled={!userId || !password}>로그인</button></form>}
      {working && <div className="knu-progress" aria-live="polite"><span className="knu-spinner" aria-hidden="true" /><div><strong>{loginAt === null ? "학교 로그인 화면을 여는 중…" : `${stage(message)}…`}</strong><small>{loginAt !== null ? `${Math.max(0, Math.round((now - loginAt) / 1000))}초` : ""}</small></div><button type="button" onClick={() => stop()}>취소</button></div>}
      {error && <p className="link-entry-error" role="alert">{error}</p>}
      {!token && !error && message && <p className="knu-status" aria-live="polite">{message}</p>}
      {result && <div className="knu-result"><strong>읽은 이수 과목 {result.courses.length}개{loginAt !== null && ` · ${Math.round((now - loginAt) / 1000)}초 걸림`}</strong>
        <ul>{result.courses.map(c => <li key={c.code}>{c.name} <small>{c.code}{c.credits != null && ` · ${c.credits}학점`}{c.category && ` · ${c.category}`}</small></li>)}</ul>
        {result.duplicates.length > 0 && <p className="link-entry-help">같은 과목코드가 여러 번 나와 하나만 남겼습니다: {result.duplicates.join(", ")}. 재이수일 수 있으니 확인해 주세요.</p>}
        <button type="button" className="primary-button" onClick={apply}>이수 과목으로 체크하기<Icon name="check" size={15} /></button></div>}
      {unmatched.length > 0 && <p className="link-entry-help">이 화면 과목 목록에 없어 체크하지 못한 과목: {unmatched.join(", ")}</p>}
    </>}
  </section>;
}
