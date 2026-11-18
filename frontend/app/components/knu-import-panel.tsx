"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { courses } from "../lib/courses";
import { buildBookmarklet, KNU_PORTAL_URL, matchImported, parseImportText, type ImportedCourse } from "../lib/knu-import";
import { Icon } from "./icons";

export function KnuImportPanel({ incoming, selected, onApply, onDismissIncoming }: { incoming: ImportedCourse[] | null; selected: string[]; onApply: (ids: string[]) => void; onDismissIncoming: () => void }) {
  const linkRef = useRef<HTMLAnchorElement>(null);
  const [pasted, setPasted] = useState<ImportedCourse[] | null>(null);
  const [pasteText, setPasteText] = useState("");
  const [error, setError] = useState("");
  const [unchecked, setUnchecked] = useState<string[]>([]);
  const [applied, setApplied] = useState("");
  const imported = pasted ?? incoming;
  const result = useMemo(() => imported ? matchImported(imported, courses) : null, [imported]);

  // React는 javascript: 주소를 막으므로 북마클릿 주소는 직접 넣는다.
  useEffect(() => {
    if (linkRef.current) linkRef.current.setAttribute("href", buildBookmarklet(window.location.href));
  }, []);

  function readPaste() {
    const list = parseImportText(pasteText);
    if (!list) { setError("형식을 알아보지 못했어요. 북마클릿의 '복사하기'로 복사한 내용이나 조회 응답 JSON을 붙여 넣어 주세요."); return; }
    setError(""); setUnchecked([]); setApplied(""); setPasted(list);
  }
  function apply() {
    if (!result) return;
    const ids = result.matched.map(m => m.course.id).filter(id => !unchecked.includes(id));
    onApply(ids);
    const added = ids.filter(id => !selected.includes(id)).length;
    setApplied(`${ids.length}개 과목을 이수로 체크했어요${added < ids.length ? ` (새로 추가 ${added}개)` : ""}.`);
  }
  function reset() { setPasted(null); setPasteText(""); setUnchecked([]); setApplied(""); setError(""); onDismissIncoming(); }

  return <section className="academic-link-entry knu-import" aria-labelledby="knu-import-title">
    <div className="document-heading"><div><span className="step-label">IMPORT FROM KNU</span><h2 id="knu-import-title">통합정보시스템에서 이수 과목 불러오기</h2></div><span className="link-entry-icon"><Icon name="link" size={35} /></span></div>
    {!result ? <>
      <ol className="knu-import-steps">
        <li>아래 <strong>Plann 이수 과목 가져오기</strong> 버튼을 북마크바로 끌어다 놓으세요. (처음 한 번만)</li>
        <li><a href={KNU_PORTAL_URL} target="_blank" rel="noreferrer">통합정보시스템</a>에 로그인하고 <strong>이수성적 조회</strong> 화면을 여세요.</li>
        <li>북마크바의 버튼을 누른 뒤 화면의 <strong>[조회]</strong> 버튼을 다시 누르세요.</li>
        <li>오른쪽 위에 뜬 상자에서 <strong>Plann으로 보내기</strong>를 누르면 이 화면에서 확인할 수 있어요.</li>
      </ol>
      <div className="knu-import-actions"><a ref={linkRef} className="primary-button knu-bookmarklet" onClick={e => e.preventDefault()} draggable>Plann 이수 과목 가져오기</a><small>여기서 누르지 말고 북마크바로 끌어 주세요.</small></div>
      <p className="link-entry-help">아이디·비밀번호는 받지 않아요. 학생 브라우저에서 조회 결과를 읽고 성적은 지운 뒤 과목코드·과목명·학점·구분만 넘깁니다. F·NP 과목과 아직 성적이 없는 수강 중 과목(2026년 2학기)은 빠져요.</p>
      <details className="knu-import-paste"><summary>보내기가 안 되면 붙여 넣기</summary>
        <textarea aria-label="복사한 이수 과목" value={pasteText} onChange={e => { setPasteText(e.target.value); setError(""); }} placeholder="북마클릿의 '복사하기'로 복사한 내용을 붙여 넣으세요" rows={4} />
        <button type="button" className="primary-button" onClick={readPaste} disabled={!pasteText.trim()}>불러오기</button>
        {error && <p className="link-entry-error" role="alert">{error}</p>}
      </details>
    </> : <div aria-live="polite">
      <p className="document-description">불러온 {imported!.length}개 중 <strong>{result.matched.length}개</strong>가 Plann 과목 목록과 맞아요. 확인 후 체크를 풀 과목은 풀고 <strong>이수로 체크</strong>를 눌러 주세요.</p>
      <div className="course-list knu-import-list">{result.matched.map(({ imported: item, course }) => <label key={course.id} className={`course-row ${unchecked.includes(course.id) ? "" : "checked"}`}><input type="checkbox" checked={!unchecked.includes(course.id)} onChange={() => setUnchecked(prev => prev.includes(course.id) ? prev.filter(id => id !== course.id) : [...prev, course.id])} /><span className="course-file"><Icon name="book" size={18} /></span><span className="course-name"><strong>{course.name}</strong><small>{item.code}{selected.includes(course.id) && " · 이미 체크됨"}</small></span><span className="course-category">{item.category || course.category}</span><span className="course-credit">{item.credits === null ? "학점 미기재" : `${item.credits}학점`}</span></label>)}</div>
      {result.unmatched.length > 0 && <details className="knu-import-unmatched"><summary>목록에 없는 과목 {result.unmatched.length}개 (이번 학기 미개설 등)</summary><ul>{result.unmatched.map(item => <li key={item.code}>{item.name} <small>{item.code}{item.credits !== null && ` · ${item.credits}학점`}</small></li>)}</ul></details>}
      <div className="knu-import-actions"><button type="button" className="primary-button" onClick={apply} disabled={!result.matched.length}>이수로 체크<Icon name="check" size={15} /></button><button type="button" className="knu-import-reset" onClick={reset}>{applied ? "닫기" : "취소"}</button></div>
      {applied && <div className="link-entry-saved"><span><Icon name="check" size={15} />{applied}</span></div>}
    </div>}
  </section>;
}
