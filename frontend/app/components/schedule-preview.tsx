"use client";
import { courses } from "../lib/courses";
import { Icon } from "./icons";
export function SchedulePreview({ selected, credits, freeDay }: { selected: string[]; credits: number; freeDay: string }) {
  const remaining = courses.filter(c => !selected.includes(c.id));
  return <section className="schedule-preview"><div className="schedule-summary"><span className="badge">시간표 준비</span><span>희망 {credits}학점</span><span>{freeDay === "없음" ? "공강 지정 없음" : `${freeDay}요일 공강 희망`}</span></div><div className="cohort-note"><strong>과목은 정리했어요. 실제 시간표에는 추가 정보가 필요해요.</strong><p>첨부 PDF에는 과목별 학점·강의 시간·개설 학기가 없습니다. 희망 조건은 저장하며, 임의 학점이나 강의 시간을 넣어 시간표를 만들지 않습니다.</p></div><div className="section-heading"><h2>미이수 문서 수록 과목<span>{remaining.length}개</span></h2></div><p className="document-description">아래는 문서에 등장하는 미체크 과목 목록입니다. 본인 전공의 개설 과목 또는 수강 가능한 과목 목록을 뜻하지 않습니다.</p><div className="candidate-list">{remaining.map(c => <div key={c.id}><Icon name="book" size={16} /><span>{c.name}</span><small>학점·시간 미기재</small></div>)}</div>{!remaining.length && <div className="empty-state"><p>문서 수록 과목을 모두 체크했어요. 졸업요건은 별도로 확인해 주세요.</p></div>}<div className="tip"><Icon name="info" size={17} /><p>실제 시간표를 구성하려면 해당 학기의 수강편람(과목별 학점, 요일·시간, 분반)이 필요합니다. 졸업요건과 선후수 과목은 이수 과목 화면에서 확인할 수 있습니다.</p></div></section>;
}
