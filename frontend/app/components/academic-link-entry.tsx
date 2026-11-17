"use client";
import { useState, type FormEvent } from "react";
import { normalizeAcademicLink } from "../lib/academic-link";
import { Icon } from "./icons";

export function AcademicLinkEntry({ savedLink, onSave, onContinue, submitLabel = "링크 저장", disabled = false }: { savedLink: string; onSave: (link: string) => void; onContinue?: () => void; submitLabel?: string; disabled?: boolean }) {
  const [error, setError] = useState("");
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (disabled) return;
    const link = normalizeAcademicLink(new FormData(event.currentTarget).get("academicLink"));
    if (!link) { setError("http:// 또는 https://로 시작하는 올바른 링크를 입력해 주세요."); return; }
    setError("");
    onSave(link);
    onContinue?.();
  }
  return <section className="academic-link-entry" aria-labelledby="academic-link-title">
    <div className="document-heading"><div><span className="step-label">START WITH A LINK</span><h2 id="academic-link-title">학적 링크로 시작하기</h2></div><span className="link-entry-icon"><Icon name="link" size={35} /></span></div>
    <p className="document-description">학적·이수내역을 제공하는 링크가 있다면 여기에 붙여 넣어 주세요.</p>
    <form onSubmit={submit} noValidate><label htmlFor="academic-link">학적·이수내역 링크</label><div className="academic-link-input-row"><input key={savedLink} id="academic-link" name="academicLink" type="url" inputMode="url" maxLength={2048} defaultValue={savedLink} placeholder="https://…" autoComplete="off" spellCheck={false} aria-invalid={!!error} aria-describedby="academic-link-help academic-link-status" onChange={() => setError("")} /><button type="submit" className="primary-button" disabled={disabled}>{submitLabel}<Icon name="arrow" size={15} /></button></div></form>
    <p id="academic-link-help" className="link-entry-help">현재는 링크만 이 브라우저에 저장합니다. 학적·과목·학점 자동 불러오기는 아직 연결되지 않았습니다.</p>
    <div id="academic-link-status" aria-live="polite">{error ? <p className="link-entry-error" role="alert">{error}</p> : savedLink ? <div className="link-entry-saved"><span><Icon name="check" size={15} />링크 저장됨 · 학업 정보는 아직 가져오지 않았어요.</span><button type="button" onClick={() => { onSave(""); setError(""); }}>링크 삭제</button></div> : <p className="link-entry-idle">링크가 없다면 직접 입력으로 시작할 수 있어요.</p>}</div>
  </section>;
}
