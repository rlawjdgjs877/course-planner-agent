import type { Course } from "./courses";

// 경북대 통합정보시스템(knuin) '이수성적 조회' 응답에서 이수 과목만 꺼내 Plann 체크 목록과 맞춘다.
// 성적 값은 F·NP와 아직 성적이 없는 과목(수강 중인 2026-2 등)을 거르는 데만 쓰고 남기지 않는다.

export const KNU_IMPORT_HASH = "#knu-import=";
export const KNU_PORTAL_URL = "https://knuin.knu.ac.kr";
const RESPONSE_MARKER = "searchTotalGradsInqrList";
const MAX_COURSES = 300;

export type ImportedCourse = { code: string; name: string; credits: number | null; category: string };
export type ImportMatch = { imported: ImportedCourse; course: Course };
export type ImportResult = { matched: ImportMatch[]; unmatched: ImportedCourse[] };

function text(value: unknown, max = 100): string {
  return typeof value === "string" || typeof value === "number" ? String(value).trim().slice(0, max) : "";
}

function credits(value: unknown): number | null {
  const n = Number(text(value));
  return Number.isFinite(n) && n > 0 && n < 30 ? n : null;
}

function dedupe(list: ImportedCourse[]): ImportedCourse[] {
  const seen = new Set<string>();
  return list.filter(c => c.code && c.name && !seen.has(c.code) && seen.add(c.code)).slice(0, MAX_COURSES);
}

// 학교 응답 원본({ data: [...] })의 행을 과목으로 바꾼다.
export function coursesFromKnuRows(rows: unknown[]): ImportedCourse[] {
  const out: ImportedCourse[] = [];
  for (const row of rows) {
    if (!row || typeof row !== "object") continue;
    const r = row as Record<string, unknown>;
    const grade = text(r.gradsGradCd).toUpperCase();
    if (!grade || grade === "F" || grade === "NP") continue;
    out.push({ code: text(r.sbjetCd, 20), name: text(r.sbjetNm), credits: credits(r.crdit), category: text(r.sbjetSctnm) });
  }
  return dedupe(out);
}

// 북마클릿이 보낸 값, 복사한 값, 또는 학교 응답 원본 JSON을 모두 받는다. 형식이 다르면 null.
export function parseImportText(input: string): ImportedCourse[] | null {
  if (!input || input.length > 500_000) return null;
  let data: unknown;
  try { data = JSON.parse(input.trim()); } catch { return null; }
  if (!data || typeof data !== "object") return null;
  const obj = data as Record<string, unknown>;
  if (Array.isArray(obj.data)) return coursesFromKnuRows(obj.data);
  if (obj.v === 1 && Array.isArray(obj.courses)) {
    return dedupe(obj.courses.flatMap(item => {
      if (!item || typeof item !== "object") return [];
      const c = item as Record<string, unknown>;
      return [{ code: text(c.c, 20), name: text(c.n), credits: credits(c.k), category: text(c.t) }];
    }));
  }
  return null;
}

export function readImportHash(hash: string): ImportedCourse[] | null {
  if (!hash.startsWith(KNU_IMPORT_HASH)) return null;
  try { return parseImportText(decodeURIComponent(hash.slice(KNU_IMPORT_HASH.length))); } catch { return null; }
}

const normalize = (name: string) => name.replace(/[\s·()[\]（）]/g, "").toLowerCase();

// 과목코드로 먼저 맞추고, 코드가 없는 문서 수록 과목은 과목명으로 맞춘다.
export function matchImported(imported: ImportedCourse[], catalog: Course[]): ImportResult {
  const byCode = new Map<string, Course>();
  const byName = new Map<string, Course>();
  for (const course of catalog) {
    if (course.code && !byCode.has(course.code)) byCode.set(course.code, course);
    const key = normalize(course.name);
    if (!byName.has(key)) byName.set(key, course);
  }
  const matched: ImportMatch[] = [];
  const unmatched: ImportedCourse[] = [];
  const used = new Set<string>();
  for (const item of imported) {
    const course = byCode.get(item.code) ?? byName.get(normalize(item.name));
    if (course && !used.has(course.id)) { used.add(course.id); matched.push({ imported: item, course }); }
    else if (!course) unmatched.push(item);
  }
  return { matched, unmatched };
}

// 학생 브라우저의 knuin 탭에서 실행되는 북마클릿. 조회 응답을 가로채 이수 과목만 Plann 주소로 넘긴다.
// 아이디·비밀번호나 성적은 읽거나 보내지 않는다.
export function buildBookmarklet(plannUrl: string): string {
  const target = JSON.stringify(plannUrl.split("#")[0] + KNU_IMPORT_HASH);
  const code = `(function(){var T=${target},M=${JSON.stringify(RESPONSE_MARKER)};
function box(){var d=document.getElementById("plann-import");if(!d){d=document.createElement("div");d.id="plann-import";d.style.cssText="position:fixed;z-index:2147483647;top:16px;right:16px;width:300px;padding:14px 16px;background:#1f2a37;color:#fff;font:13px/1.6 sans-serif;border-radius:10px;box-shadow:0 8px 28px rgba(0,0,0,.35)";document.body.appendChild(d);}return d;}
function say(t){var d=box();d.textContent=t;return d;}
function btn(d,label,fn){var b=document.createElement("button");b.textContent=label;b.style.cssText="margin:10px 8px 0 0;padding:6px 12px;border:0;border-radius:6px;background:#2994fc;color:#fff;font:inherit;cursor:pointer";b.onclick=fn;d.appendChild(b);return b;}
function handle(raw){try{var j=typeof raw==="string"?JSON.parse(raw):raw;var rows=j&&j.data;if(!Array.isArray(rows))return;var out=[],seen={};
rows.forEach(function(r){var g=String(r.gradsGradCd==null?"":r.gradsGradCd).trim().toUpperCase();if(!g||g==="F"||g==="NP")return;var c=String(r.sbjetCd||"").trim(),n=String(r.sbjetNm||"").trim();if(!c||!n||seen[c])return;seen[c]=1;out.push({c:c,n:n,k:Number(r.crdit)||null,t:String(r.sbjetSctnm||"").trim()});});
var p=JSON.stringify({v:1,courses:out});var d=say("이수 과목 "+out.length+"개를 읽었어요. 성적은 빼고 과목만 보냅니다.");
btn(d,"Plann으로 보내기",function(){window.open(T+encodeURIComponent(p),"_blank");});
btn(d,"복사하기",function(e){var b=e.target;navigator.clipboard.writeText(p).then(function(){b.textContent="복사됨";},function(){b.textContent="복사 실패";});});
}catch(e){say("조회 결과를 읽지 못했어요. 다시 조회해 주세요.");}}
if(!window.__plannImport){window.__plannImport=1;var X=XMLHttpRequest.prototype,o=X.open,s=X.send;
X.open=function(m,u){this.__plannUrl=String(u||"");return o.apply(this,arguments);};
X.send=function(){var x=this;if(x.__plannUrl.indexOf(M)>=0)x.addEventListener("load",function(){handle(x.responseType===""||x.responseType==="text"?x.responseText:x.response);});return s.apply(this,arguments);};
var f=window.fetch;if(f)window.fetch=function(i){var u=typeof i==="string"?i:(i&&i.url)||"";var r=f.apply(this,arguments);if(String(u).indexOf(M)>=0)r.then(function(res){res.clone().text().then(handle);});return r;};}
say("준비됐어요. 이수성적 조회 화면에서 [조회] 버튼을 다시 눌러 주세요.");})();`;
  return "javascript:" + encodeURIComponent(code.replace(/\n/g, ""));
}
