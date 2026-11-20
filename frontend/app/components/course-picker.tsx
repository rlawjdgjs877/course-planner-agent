"use client";
import { useId, useMemo, useState } from "react";
import { courseOfferings } from "../lib/offerings";

type Option = { value: string; label: string; detail: string; search: string };
const normalize = (text: string) => text.replace(/\s+/g, "").toLowerCase();

/** 과목코드를 외우지 않아도 과목명·교수명으로 찾아 넣는다. 과목 전체(모든 분반) 또는 특정 분반을 고를 수 있다. */
const options: Option[] = (() => {
  const subjects = new Map<string, Option>();
  const sections: Option[] = [];
  for (const offering of courseOfferings) {
    const r = offering.records[0];
    if (!subjects.has(r.sbjetCd)) subjects.set(r.sbjetCd, { value: r.sbjetCd, label: r.sbjetNm, detail: `${r.sbjetCd} · 모든 분반`, search: normalize(`${r.sbjetNm}${r.sbjetCd}`) });
    sections.push({ value: r.crseNo, label: `${r.sbjetNm} ${r.sbjetDvnno}분반`, detail: `${r.totalPrfssNm || "교수 미정"} · ${r.lssnsRealTimeInfo || "시간 미정"}`, search: normalize(`${r.sbjetNm}${r.crseNo}${r.totalPrfssNm}`) });
  }
  return [...subjects.values(), ...sections];
})();
const labelOf = new Map(options.map(o => [o.value, o.label]));

type Props = { label: string; value: string[]; onChange: (next: string[]) => void; placeholder: string };

export function CoursePicker({ label, value, onChange, placeholder }: Props) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const listId = useId();
  const matches = useMemo(() => {
    const q = normalize(query);
    if (!q) return [];
    return options.filter(o => o.search.includes(q) && !value.includes(o.value)).slice(0, 12);
  }, [query, value]);
  function add(item: string) {
    const clean = item.trim();
    if (clean && !value.includes(clean)) onChange([...value, clean]);
    setQuery(""); setOpen(false);
  }
  return <div className="document-field course-picker">{label}
    {value.length > 0 && <div className="course-picker-chips">{value.map(item => <span key={item}>{labelOf.get(item) ?? item}{labelOf.has(item) && <small>{item}</small>}<button type="button" aria-label={`${labelOf.get(item) ?? item} 빼기`} onClick={() => onChange(value.filter(v => v !== item))}>×</button></span>)}</div>}
    <div className="course-picker-suggest">
      <input role="combobox" aria-label={label} aria-controls={listId} aria-autocomplete="list" aria-expanded={open && matches.length > 0} placeholder={placeholder} value={query}
        onChange={e => { setQuery(e.target.value); setOpen(true); }} onFocus={() => setOpen(true)} onBlur={() => window.setTimeout(() => setOpen(false), 150)}
        onKeyDown={e => { if (e.key === "Enter") { e.preventDefault(); if (matches[0]) add(matches[0].value); else if (/^[A-Za-z]{4}\d{4}(-\d{3})?$/.test(query.trim())) add(query.trim().toUpperCase()); } }} />
      {open && matches.length > 0 && <ul id={listId} role="listbox">{matches.map(o => <li key={o.value} role="option" aria-selected="false"><button type="button" onMouseDown={e => e.preventDefault()} onClick={() => add(o.value)}><span>{o.label}</span><small>{o.detail}</small></button></li>)}</ul>}
    </div>
  </div>;
}
