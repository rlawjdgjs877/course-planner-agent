"use client";
import { courses } from "../lib/courses";
import { CourseOfferings } from "./course-offerings";
import { courseImportReport } from "../lib/offerings";
import { Icon } from "./icons";

export function SchedulePreview({ selected, credits, freeDay }: { selected: string[]; credits: number; freeDay: string }) {
  const completedNames = courses.filter(c => selected.includes(c.id)).map(c => c.name);
  return <section className="schedule-preview"><div className="schedule-summary"><span className="badge">개설 강좌 확인</span><span>희망 {credits}학점</span><span>{freeDay === "없음" ? "공강 지정 없음" : `${freeDay}요일 공강 희망`}</span></div><div className="cohort-note"><strong>이수 체크한 과목을 제외하고 개설 강좌를 살펴보세요.</strong><p>2026년 2학기 {courseImportReport.offeringCount}개 분반을 반영했습니다. 아래 목록은 수강 가능 여부를 확정한 추천 시간표가 아닙니다. 희망 학점·공강에 맞춘 자동 생성과 분반 선택은 아직 연결되지 않았습니다.</p></div><CourseOfferings excludeNames={completedNames} /><div className="tip"><Icon name="info" size={17} /><p>교환학점·대체 인정·실제 이수학점은 별도 확인이 필요합니다. 주말 수업과 시간이 미기재된 강좌는 임의로 평일에 배치하지 않습니다.</p></div></section>;
}
