"use client";
import { useEffect, useRef } from "react";
import { SchoolImportPanel } from "./school-import-panel";
import type { ImportedCourse } from "../lib/imported-courses";
export function SchoolImportDialog({ onClose, onApply }: { onClose: () => void; onApply: (courses: ImportedCourse[]) => void }) {
  const dialog = useRef<HTMLDivElement>(null);
  const close = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    close.current?.focus();
    const keys = (event: KeyboardEvent) => {
      if (event.defaultPrevented) return;
      if (event.key === "Escape") { event.preventDefault(); onClose(); return; }
      if (event.key !== "Tab") return;
      const focusable = [...(dialog.current?.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), summary, [tabindex="0"]') ?? [])].filter(el => el.getClientRects().length);
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (!first) return;
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", keys);
    return () => { document.body.style.overflow = overflow; document.removeEventListener("keydown", keys); previousFocus?.focus(); };
  }, [onClose]);
  return <div className="school-dialog-backdrop"><div ref={dialog} className="school-import-dialog" role="dialog" aria-modal="true" aria-labelledby="school-dialog-title"><header className="school-dialog-header"><div><strong id="school-dialog-title">경북대학교 학교 로그인</strong><span>Plann 안에서 학교 화면에 직접 로그인해 주세요.</span></div><button ref={close} type="button" onClick={onClose} aria-label="학교 로그인 창 닫기">닫기 ×</button></header><SchoolImportPanel autoStart onApply={onApply} /></div></div>;
}

