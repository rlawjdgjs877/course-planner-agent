"""'나의 시간표' 화면의 AI 에이전트.

원칙: 조합 탐색과 검증은 코드(planner.generate)가, 말 이해와 설명은 AI 가 맡는다.
AI 는 과목·시간·학점을 지어내지 않고, 도구(app/agent/agent_tools.py)로 확인한 것만 말한다.

1. message 가 없으면 지금 후보를 왜 이렇게 짰는지 설명한다.
   코드가 사실 목록(explain_facts)을 만들고, 키가 있으면 AI 가 그 사실만으로 문장을 다듬는다.
2. message 가 있으면
   - OPENAI_API_KEY 와 OPENAI_MODEL 이 있으면 AI 에이전트가 도구를 불러 가며(최대 5스텝)
     과목을 찾고, 선수과목을 확인하고, 조건을 바꿔 시간표를 실제로 다시 만든다.
   - 키가 없거나 AI 가 실패하면 자주 쓰는 말을 규칙(parse_rules)으로 알아듣는다.
   어느 쪽이든 무엇을 했는지 steps 로 돌려준다 (화면에 '에이전트가 한 일'로 보인다).
"""

import logging
import os
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from app.schemas import (
    Candidate,
    ChatMessage,
    Course,
    DayTime,
    GenerateTimetableRequest,
    GenerateTimetableResponse,
)
from app.services import planner
from app.services.timetable import validate_timetable

logger = logging.getLogger(__name__)

WEEKDAYS = ("월", "화", "수", "목", "금")
HISTORY_LIMIT = 8
REASONS = {
    "not_offered": "이번 학기 미개설", "already_completed": "이미 이수", "excluded": "제외 목록에 있음",
    "not_recommended": "자동 추천 제외", "free_day_conflict": "공강 요일과 겹침",
    "blocked_time": "비울 시간과 겹침", "time_conflict": "다른 필수 과목과 겹침",
}


class PlanChatRequest(BaseModel):
    message: str | None = Field(default=None, max_length=500, description="비우면 지금 시간표를 설명만 한다")
    request: GenerateTimetableRequest = Field(description="지금 시간표를 만든 조건")
    candidate_id: str | None = Field(default=None, description="지금 보고 있는 후보. 이 후보를 바탕으로 고친다")
    candidate_ids: list[str] = Field(
        default_factory=list, description="화면의 후보 탭 id 를 순서대로 (1안, 2안 …). 'N안 보여줘'에 쓴다"
    )
    history: list[ChatMessage] = Field(default_factory=list)


class AgentStep(BaseModel):
    """에이전트가 한 일 한 줄. 화면에 차례대로 보여 준다."""

    tool: str = Field(description="부른 도구 이름. 예: search_courses, apply_changes, rules")
    label: str = Field(description="화면 표시용 한 줄. 예: 과목 검색: 운영체제")
    detail: str = Field(default="", description="결과 한 줄. 예: 3개 찾음")
    ok: bool = True


class PlanChatResponse(BaseModel):
    reply: str
    applied: bool = Field(description="조건이 바뀌어 시간표를 다시 만들었는지")
    request: GenerateTimetableRequest = Field(description="적용된 조건 (바뀌지 않았으면 보낸 그대로)")
    response: GenerateTimetableResponse | None = Field(default=None, description="다시 만든 시간표")
    steps: list[AgentStep] = Field(default_factory=list, description="에이전트가 한 일 (도구 호출 순서)")
    mode: Literal["ai", "rules"] = Field(default="rules", description="ai: 도구를 쓰는 AI 에이전트, rules: 규칙")
    previous_candidate_id: str | None = Field(default=None, description="바꾸기 전 후보 id (바뀐 칸 강조용)")
    select_candidate: str | None = Field(default=None, description="화면에서 이 후보 탭으로 바꾼다. 예: tt_002")


class Edit(BaseModel):
    """말 한마디를 조건 수정으로 바꾼 것. AI 도구(apply_changes)와 규칙이 같은 모양을 쓴다."""

    reply: str = Field(default="", description="학생에게 할 짧은 답 (무엇을 바꿨는지)")
    add: list[str] = Field(default_factory=list, description="넣을 과목 (과목코드나 과목명)")
    remove: list[str] = Field(default_factory=list, description="뺄 과목 (과목코드나 과목명)")
    add_category: str | None = Field(default=None, description="이 구분(교양, 전공) 과목을 하나 골라 넣는다")
    remove_category: str | None = Field(default=None, description="지금 시간표에서 이 구분(교양, 전공) 과목을 하나 뺀다")
    free_days: list[str] = Field(default_factory=list, description="반드시 비울 요일 (한 글자)")
    unfree_days: list[str] = Field(default_factory=list, description="공강을 풀 요일")
    allow_weekend: bool | None = Field(default=None, description="주말 수업도 넣어도 되는지")
    no_class_before: int | None = Field(default=None, description="평일 이 시각(0~23) 전에는 수업 없음")
    no_class_after: int | None = Field(default=None, description="평일 이 시각(1~24) 뒤에는 수업 없음")
    target_credits: float | None = Field(default=None, description="목표 학점")
    credits_delta: float | None = Field(default=None, description="지금 학점에서 늘리거나(+) 줄일(-) 학점")


# ---------- 작은 도움 함수 ----------


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _key(name: str) -> str:
    """'운영체제(샘플)' → '운영체제'. 학생은 괄호 부분을 빼고 말한다."""
    return re.sub(r"\(.*?\)", "", _compact(name))


def _eul(word: str) -> str:
    """을/를."""
    last = _key(word)[-1:] or word[-1:]
    if "가" <= last <= "힣":
        return "을" if (ord(last) - 0xAC00) % 28 else "를"
    return "을(를)"


def _mentioned(text: str, name: str) -> bool:
    key = _key(name)
    return len(key) >= 2 and key in _compact(text)


def _is_category(category: str | None, wanted: str) -> bool:
    category = category or ""
    if wanted == "전공":
        return "전공" in category
    return wanted in category


def summarize(candidate: Candidate | None) -> dict | None:
    """후보를 AI 와 화면이 읽기 좋은 짧은 모양으로."""
    if candidate is None:
        return None
    return {
        "id": candidate.id,
        "total_credits": candidate.total_credits,
        "free_days": candidate.free_days,
        "warnings": candidate.warnings,
        "sections": [
            {"code": s.course_code, "name": s.name, "category": s.category, "credits": s.credits, "time": s.time_raw, "professor": s.professor}
            for s in candidate.sections
        ],
    }


def verify(candidate: Candidate) -> tuple[int, list[str]]:
    """코드로 다시 검증한다. (시간 겹침 수, 문제 목록)"""
    problems = validate_timetable(candidate.sections)
    return sum(1 for p in problems if p.startswith("시간이 겹칩니다")), problems


# ---------- 선수과목 (다른 모듈이 있으면 쓴다) ----------


def prerequisite_check(course: str, completed: list[str], catalog: list[Course], track: str | None = None) -> list[dict] | None:
    """app.services.prerequisites.check 를 부른다. 모듈이나 자료가 없으면 None ('데이터 없음')."""
    try:
        from app.services import prerequisites
    except ImportError:
        return None
    check = getattr(prerequisites, "check", None)
    if check is None:
        return None
    try:
        try:
            rows = check(course, completed, catalog, track=planner.resolve_track(track))
        except TypeError:  # 트랙을 안 받는 이전 모양
            rows = check(course, completed, catalog)
    except Exception:  # 자료가 깨졌어도 챗봇은 계속 답한다
        logger.exception("선수과목 확인 실패: %s", course)
        return None
    return [row if isinstance(row, dict) else {"name": str(row)} for row in rows] if rows is not None else None


def prerequisite_items(rows: list[dict]) -> list[tuple[str, bool | None]]:
    """check() 결과를 (선수과목 이름, 이수 여부) 로 읽는다. 키 이름이 조금 달라도 읽는다."""
    items = []
    for row in rows:
        name = next((str(row[k]) for k in ("required", "name", "prerequisite", "prereq", "course", "code") if row.get(k)), "")
        done = next((bool(row[k]) for k in ("completed", "satisfied", "done", "taken", "ok", "met") if k in row), None)
        if name:
            items.append((name, done))
    return items


def prerequisite_reason(section: Course, completed: list[str], catalog: list[Course], track: str | None = None) -> str | None:
    """선수과목 사슬 근거. 예: '자료구조를 들었으니 이어서 듣는 과목 (공통 · 프로그래밍)'.

    이수 과목을 모르면(completed 가 비면) 미이수라고 단정하지 않는다 (planner 경고가 따로 알린다)."""
    rows = prerequisite_check(section.course_code, completed, catalog, track)
    if not rows:
        return None
    items = prerequisite_items(rows)
    done = [n for n, ok in items if ok]
    missing = [n for n, ok in items if ok is False]
    chain = next((str(r["chain"]) for r in rows if r.get("chain")), "")
    tail = f" ({chain})" if chain else ""
    if done:
        return f"{'·'.join(done)}{_eul(done[-1])} 들었으니 이어서 듣는 과목{tail}"
    if missing and completed:
        return f"선수과목 {'·'.join(missing)} 이수 기록이 없어 (권장 순서 확인 필요){tail}"
    return None


# ---------- 설명 ----------


def section_reasons(section: Course, request: GenerateTimetableRequest, catalog: list[Course] | None = None) -> list[str]:
    track_id = planner.resolve_track(request.track)
    track = planner.TRACKS.get(track_id or "")
    must = {code for item in request.must_include for code in (item, item.split("-")[0])}
    why = []
    if section.course_id in must or section.course_code in must or section.name in must:
        why.append("네가 꼭 넣어 달라고 한 과목")
    sources = {listing.source for listing in section.listings}
    if section.category != "교양" and (track_id in sources or "computing" in sources):
        why.append(f"{track + ' ' if track else '컴학 '}{section.category} 과목")
    elif section.area:
        why.append(f"교양 {section.area}" + (" (희망 영역)" if section.area in request.ge_areas else ""))
    if request.grade and section.grade == str(request.grade):
        why.append(f"{request.grade}학년 대상")
    if section.professor and section.professor in request.prefer_professor:
        why.append("선호 교수")
    if catalog is not None and (chain := prerequisite_reason(section, request.completed, catalog, request.track)):
        why.append(chain)
    return why


def explain_facts(
    candidate: Candidate,
    request: GenerateTimetableRequest,
    response: GenerateTimetableResponse | None = None,
    catalog: list[Course] | None = None,
) -> list[str]:
    """시간표에 대한 사실 목록. 템플릿 설명과 AI 설명이 모두 이것만 근거로 쓴다."""
    lines = [f"이 시간표는 {len(candidate.sections)}과목 {candidate.total_credits:g}학점이야 (목표 {request.target_credits:g}학점)."]
    for section in candidate.sections:
        why = section_reasons(section, request, catalog)
        lines.append(f"• {section.name}: {', '.join(why) or '학점을 채우면서 다른 과목과 시간이 안 겹쳐서'}")
    if request.free_days:
        lines.append(f"{'·'.join(request.free_days)}요일은 비워 달라고 해서 수업을 안 넣었어.")
    if candidate.free_days:
        lines.append(f"평일 공강: {'·'.join(candidate.free_days)}요일.")
    lines.append(f"수업 사이 빈 시간은 합쳐서 {candidate.gap_minutes / 60:.1f}시간으로 줄이려고 했어.")
    for warning in candidate.warnings:
        lines.append(f"주의: {warning}")
    if response:
        for omitted in response.omitted_required:
            lines.append(f"못 넣은 과목: {omitted.name or omitted.item} ({REASONS.get(omitted.reason, omitted.reason)}).")
        for warning in response.warnings:
            lines.append(f"주의: {warning}")
    return list(dict.fromkeys(lines))  # 후보 경고와 응답 경고가 겹치면 한 번만


EXAMPLES = "바꾸고 싶은 게 있으면 말해 줘. 예: '○○ 빼줘', '금요일 비워줘', '아침 수업 싫어', '15학점으로'."


def explain(
    candidate: Candidate,
    request: GenerateTimetableRequest,
    response: GenerateTimetableResponse | None = None,
    catalog: list[Course] | None = None,
) -> str:
    return "\n".join([*explain_facts(candidate, request, response, catalog), EXAMPLES])


# ---------- 말 알아듣기 (규칙) ----------


def _days(text: str) -> list[str]:
    return [day for day in "월화수목금토일" if re.search(fr"{day}(요일|욜)", text)]


def parse_rules(message: str, candidate: Candidate | None, catalog: list[Course]) -> Edit:
    """AI 없이 알아듣는 말. 못 알아들으면 빈 Edit 을 돌려준다."""
    text = _compact(message)
    edit = Edit()
    current = candidate.sections if candidate else []
    names = sorted({c.name: c for c in catalog}.values(), key=lambda c: len(_key(c.name)), reverse=True)
    if re.search(r"빼|제외|지워|없애|싫", text):
        edit.remove = [s.course_code for s in current if _mentioned(text, s.name)]
        if not edit.remove:  # 시간표에 없는 과목을 말했으면 apply 가 "없어"라고 알려 준다
            edit.remove = [c.course_code for c in names if _mentioned(text, c.name)][:1]
    if re.search(r"추가|넣어|넣고|담아|듣고싶|들을래", text):
        edit.add = [c.course_code for c in names if _mentioned(text, c.name)][:1]
    if not edit.add and not edit.remove:
        if re.search(r"전공위주|전공많이|전공더|전공으로채|교양말고", text):
            edit.remove_category, edit.add_category = "교양", "전공"
        elif re.search(r"교양.*(줄|빼|없애|제외)", text):
            edit.remove_category = "교양"
        elif re.search(r"전공.*(줄|빼|없애|제외)", text):
            edit.remove_category = "전공"
        elif m := re.search(r"(교양|전공).*(추가|넣어|더|늘려)", text):
            edit.add_category = m.group(1)
    days = _days(text)
    weekend_ok = re.search(r"풀|있어도|넣어도|괜찮|돼|좋아", text)
    if days and weekend_ok:
        edit.unfree_days = days
        if set(days) & {"토", "일"}:
            edit.allow_weekend = True
    elif days and re.search(r"비워|공강|없|쉬|빼", text):
        edit.free_days = days
    if re.search(r"주말.*(괜찮|돼|넣어도|있어도)", text):
        edit.allow_weekend = True
    if hour := re.search(r"(\d{1,2})시(이전|전)", text):
        edit.no_class_before = int(hour.group(1))
    elif period := re.search(r"([1-3])교시", text):
        edit.no_class_before = 9 + int(period.group(1))  # 1교시 09:00~ → 10시 전 수업 없음
    elif re.search(r"아침|오전|일찍|이른", text):
        edit.no_class_before = 10
    if hour := re.search(r"(\d{1,2})시(이후|넘어|넘|뒤|부터없)", text):
        edit.no_class_after = int(hour.group(1)) + (12 if int(hour.group(1)) < 9 else 0)
    elif re.search(r"저녁|야간|늦은", text):
        edit.no_class_after = 18
    if credits := re.search(r"(\d{1,2})학점", text):
        edit.target_credits = float(credits.group(1))
    elif re.search(r"학점.*(늘|많)", text):
        edit.credits_delta = 3
    elif re.search(r"학점.*(줄|적)", text):
        edit.credits_delta = -3
    return edit


def describe_edit(edit: Edit, catalog: list[Course]) -> str:
    """Edit 을 사람이 읽을 한 줄로 (steps 의 '말 이해')."""
    name_of = {c.course_code: c.name for c in catalog}
    parts = [f"{name_of.get(x, x)} 빼기" for x in edit.remove] + [f"{name_of.get(x, x)} 넣기" for x in edit.add]
    if edit.remove_category:
        parts.append(f"{edit.remove_category} 하나 빼기")
    if edit.add_category:
        parts.append(f"{edit.add_category} 하나 넣기")
    parts += [f"{d}요일 공강" for d in edit.free_days] + [f"{d}요일 공강 풀기" for d in edit.unfree_days]
    if edit.allow_weekend:
        parts.append("주말 수업 허용")
    if edit.no_class_before is not None:
        parts.append(f"{edit.no_class_before}시 전 수업 없음")
    if edit.no_class_after is not None:
        parts.append(f"{edit.no_class_after}시 뒤 수업 없음")
    if edit.target_credits is not None:
        parts.append(f"{edit.target_credits:g}학점")
    elif edit.credits_delta:
        parts.append(f"학점 {edit.credits_delta:+g}")
    return ", ".join(parts)


def _fits(course: Course, taken: list[Course], free_days: list[str], blocked: list[dict]) -> bool:
    from app.services.timetable import courses_conflict

    if not course.meetings or planner.not_recommended(course):
        return False
    if any(m.day in free_days for m in course.meetings):
        return False
    for block in blocked:
        for m in course.meetings:
            if m.day == block["day"] and m.start < block["end"] and block["start"] < m.end:
                return False
    return not any(courses_conflict(course, other) for other in taken)


def apply(
    edit: Edit,
    request: GenerateTimetableRequest,
    candidate: Candidate | None,
    catalog: list[Course],
    notes: list[str] | None = None,
) -> tuple[GenerateTimetableRequest, list[str]]:
    """Edit 을 조건에 반영한다. (새 조건, 바꾼 내용). 반영 못 한 이유는 notes 에 적는다."""
    notes = notes if notes is not None else []
    data = request.model_dump()
    done: list[str] = []
    name_of = {c.course_code: c.name for c in catalog} | {c.name: c.name for c in catalog}
    code_of = {c.name: c.course_code for c in catalog} | {c.course_code: c.course_code for c in catalog} | {c.course_id: c.course_code for c in catalog}
    code_of |= {_key(c.name): c.course_code for c in catalog if _key(c.name) not in code_of}
    current = candidate.sections if candidate else []
    in_current = {s.course_code for s in current}
    musts = {x.split("-")[0] for x in data["must_include"]} | set(data["must_include"])
    category_delta = 0.0

    def drop(code: str) -> None:
        data["must_include"] = [x for x in data["must_include"] if x.split("-")[0] != code and x != name_of[code]]
        data["exclude"] = [*dict.fromkeys([*data["exclude"], code])]

    for item in edit.remove:
        code = code_of.get(item) or code_of.get(_key(item))
        if not code:
            notes.append(f"'{item}' 과목을 개설 강좌에서 못 찾았어")
            continue
        if candidate is not None and code not in in_current:
            notes.append(f"{name_of[code]}{'은' if _eul(name_of[code]) == '을' else '는'} 지금 시간표에 없어")
            continue
        drop(code)
        done.append(f"{name_of[code]} 뺐어")
    for item in edit.add:
        code = code_of.get(item) or code_of.get(_key(item))
        if not code:
            notes.append(f"'{item}' 과목을 개설 강좌에서 못 찾았어")
            continue
        if code in in_current:
            notes.append(f"{name_of[code]}{'은' if _eul(name_of[code]) == '을' else '는'} 이미 들어 있어")
            continue
        data["exclude"] = [x for x in data["exclude"] if x != code and x != name_of[code]]
        data["must_include"] = [*dict.fromkeys([*data["must_include"], code])]
        done.append(f"{name_of[code]} 넣었어")
    if edit.remove_category:
        choices = [s for s in current if _is_category(s.category, edit.remove_category) and s.course_code not in musts and s.course_id not in musts]
        choices.sort(key=lambda s: ("필수" in (s.category or ""), planner.fit_bonus(s, planner.resolve_track(request.track), request.grade)))
        if choices:
            gone = choices[0]
            drop(gone.course_code)
            category_delta -= gone.credits
            current = [s for s in current if s.course_code != gone.course_code]
            done.append(f"{edit.remove_category} {gone.name} 뺐어")
        else:
            notes.append(f"지금 시간표에서 뺄 {edit.remove_category} 과목이 없어 (꼭 넣을 과목은 안 빼)")
    if edit.add_category:
        skip = {*in_current, *data["exclude"], *data["completed"]}
        options = [planner.for_track(c, planner.resolve_track(request.track)) for c in catalog if c.course_code not in skip]
        options = [c for c in options if _is_category(c.category, edit.add_category)]
        options.sort(key=lambda c: (-planner.fit_bonus(c, planner.resolve_track(request.track), request.grade), c.course_id))
        free = [*data["free_days"], *edit.free_days]
        pick = next((c for c in options if _fits(c, current, free, data["blocked_times"])), None)
        if pick:
            data["must_include"] = [*dict.fromkeys([*data["must_include"], pick.course_id])]
            category_delta += pick.credits
            done.append(f"{edit.add_category} {pick.name} 넣었어 ({pick.time_raw})")
        else:
            notes.append(f"지금 시간표와 안 겹치게 넣을 {edit.add_category} 과목이 없어")
    for day in edit.free_days:
        if day not in "월화수목금토일" or len(day) != 1 or day in data["free_days"]:
            continue
        data["free_days"].append(day)
        done.append(f"{day}요일 비웠어")
    for day in edit.unfree_days:
        if day in data["free_days"]:
            data["free_days"].remove(day)
            done.append(f"{day}요일 공강 풀었어")
    if edit.allow_weekend is not None:
        if "allow_weekend" in GenerateTimetableRequest.model_fields:
            if data.get("allow_weekend") != edit.allow_weekend:
                data["allow_weekend"] = edit.allow_weekend
                done.append("주말 수업도 넣을 수 있게 했어" if edit.allow_weekend else "주말 수업은 뺐어")
        elif edit.allow_weekend:
            notes.append("주말 수업 허용은 아직 시간표 만들기에서 지원하지 않아")
    if edit.no_class_before is not None and 1 <= edit.no_class_before <= 23:
        start = f"{edit.no_class_before:02d}:00"
        data["blocked_times"] = [b for b in data["blocked_times"] if b["start"] != "00:00"] + [{"day": d, "start": "00:00", "end": start} for d in WEEKDAYS]
        done.append(f"평일 {edit.no_class_before}시 전 수업 뺐어")
    if edit.no_class_after is not None and 1 <= edit.no_class_after <= 23:
        end = f"{edit.no_class_after:02d}:00"
        data["blocked_times"] = [b for b in data["blocked_times"] if b["end"] != "24:00"] + [{"day": d, "start": end, "end": "24:00"} for d in WEEKDAYS]
        done.append(f"평일 {edit.no_class_after}시 뒤 수업 뺐어")
    if edit.target_credits is not None or edit.credits_delta or category_delta:
        now = candidate.total_credits if candidate else request.target_credits
        if edit.target_credits is not None:
            target = edit.target_credits
        else:
            target = now + (edit.credits_delta or category_delta)
        target = max(0.0, min(float(planner.CREDIT_CAP), target))
        data["target_credits"] = target
        data["min_credits"] = min(data["min_credits"], target)
        data["max_credits"] = max(min(data["max_credits"], planner.CREDIT_CAP), target)
        if edit.target_credits is not None or edit.credits_delta:
            done.append(f"목표 {target:g}학점으로 바꿨어")
    data["blocked_times"] = [DayTime(**b) for b in data["blocked_times"]]
    return GenerateTimetableRequest(**data), done


# ---------- 조건을 바꿔 다시 만들기 (규칙과 AI 도구가 같이 쓴다) ----------


@dataclass
class Rebuild:
    request: GenerateTimetableRequest
    done: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    response: GenerateTimetableResponse | None = None
    before: Candidate | None = None

    @property
    def ok(self) -> bool:
        return bool(self.done and self.response and self.response.candidates)

    @property
    def new(self) -> Candidate | None:
        return self.response.candidates[0] if self.response and self.response.candidates else None

    def diff(self) -> tuple[list[str], list[str]]:
        before = {s.name for s in self.before.sections} if self.before else set()
        after = {s.name for s in self.new.sections} if self.new else set()
        return sorted(before - after), sorted(after - before) if self.before else []

    def summary(self) -> dict:
        """AI 에게 돌려줄 도구 결과."""
        removed, added = self.diff()
        result: dict[str, Any] = {"ok": self.ok, "changed": self.done, "notes": self.notes}
        if self.response:
            result |= {
                "status": self.response.status,
                "candidates": len(self.response.candidates),
                "warnings": self.response.warnings,
                "omitted": [f"{o.name or o.item}: {REASONS.get(o.reason, o.reason)}" for o in self.response.omitted_required],
                "alternatives": [{"relaxed": a.relaxed, "description": a.description} for a in self.response.alternatives],
            }
        if self.new:
            result |= {"removed": removed, "added": added, "timetable": summarize(self.new)}
        return result


def rebuild(edit: Edit, request: GenerateTimetableRequest, candidate: Candidate | None, catalog: list[Course]) -> Rebuild:
    notes: list[str] = []
    updated, done = apply(edit, request, candidate, catalog, notes)
    result = Rebuild(request=updated, done=done, notes=notes, before=candidate)
    if done:
        base = candidate.id if candidate else None
        result.response = planner.generate(updated.model_copy(update={"base_candidate_id": base}), catalog)
    return result


def build_steps(result: Rebuild, tool: str) -> list[AgentStep]:
    """조건 반영 → 다시 생성 → 검증 단계."""
    if not result.done:
        return [AgentStep(tool=tool, label="조건 반영", detail=", ".join(result.notes) or "바꿀 조건 없음", ok=False)]
    steps = [AgentStep(tool=tool, label=f"조건 반영: {', '.join(result.done)}", detail=f"{len(result.done)}개 바꿈")]
    response = result.response
    count = len(response.candidates) if response else 0
    detail = {"success": "모든 조건 만족", "partial": "일부 조건만 만족", "infeasible": "맞는 시간표 없음"}.get(response.status if response else "", "")
    steps.append(AgentStep(tool="generate_timetable", label=f"시간표 다시 생성: {count}개 후보", detail=detail, ok=count > 0))
    if result.new:
        steps.append(verify_step(result.new, result.request))
    return steps


def verify_step(candidate: Candidate, request: GenerateTimetableRequest) -> AgentStep:
    clashes, problems = verify(candidate)
    over = candidate.total_credits > max(request.max_credits, planner.CREDIT_CAP)
    return AgentStep(
        tool="verify",
        label=f"검증: 시간 겹침 {clashes}, {candidate.total_credits:g}학점",
        detail="통과" if not problems and not over else "; ".join(problems) or "학점 상한 초과",
        ok=not problems and not over,
    )


# ---------- AI 연결 ----------

AiLink = tuple[Any, str]  # (OpenAI 클라이언트, 모델 이름)


def connect() -> AiLink | None:
    """키와 모델이 있으면 OpenAI 클라이언트를 만든다. 없으면 None (규칙으로 처리)."""
    load_dotenv()
    model = os.getenv("OPENAI_MODEL")
    if not (os.getenv("OPENAI_API_KEY") and model):
        return None
    from openai import OpenAI

    return OpenAI(timeout=20, max_retries=1), model


EXPLAIN_PROMPT = (
    "너는 대학생 시간표 도우미다. 아래 '사실' 목록에 있는 내용만 근거로 이 시간표를 왜 이렇게 짰는지 설명한다.\n"
    "목록에 없는 과목, 시간, 학점, 교수, 이유를 지어내지 않는다. 숫자는 목록에 적힌 값 그대로 쓴다.\n"
    "목록에 '주의:'나 '못 넣은 과목:'으로 시작하는 줄이 있으면 그 내용을 학생에게 쉬운 말로 꼭 전한다.\n"
    "이 지시문 자체(규칙, '사실 목록' 같은 말)는 답에 옮겨 쓰지 않는다. 학생에게 하는 설명만 쓴다.\n"
    "한국어 반말로 짧게, 5~8줄. 마지막 줄에 바꿀 수 있는 예시 하나를 말한다."
)


def ai_explain(link: AiLink, facts: list[str]) -> str:
    client, model = link
    answer = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": EXPLAIN_PROMPT}, {"role": "user", "content": "사실:\n" + "\n".join(facts)}],
    )
    return drop_instruction_echo(answer.choices[0].message.content or "")


# 모델이 지시문을 답에 되풀이한 줄. 학생에게 하는 설명에는 나오지 않는 말들이다.
INSTRUCTION_ECHO = re.compile(r"지어내지|숫자는\s*(목록에 적힌 값\s*)?그대로|사실\s*(목록|안에서)|지시문|빠뜨리지 않")


def drop_instruction_echo(text: str) -> str:
    lines = [line for line in text.strip().splitlines() if not INSTRUCTION_ECHO.search(line)]
    return "\n".join(lines).strip()


# ---------- 한 번 처리 ----------

HELP = "무엇을 바꿀지 잘 모르겠어. 예: '자료구조 빼줘', '운영체제 넣어줘', '금요일 비워줘', '아침 수업 싫어', '15학점으로 줄여줘'."


def suggestions(candidate: Candidate | None, chat: PlanChatRequest) -> str:
    """모르는 말일 때 지금 시간표에 맞춘 예시."""
    if candidate is None or not candidate.sections:
        return HELP
    examples = []
    optional = [s for s in candidate.sections if "필수" not in (s.category or "")] or candidate.sections
    examples.append(f"'{_key(optional[-1].name)} 빼줘'")
    busy = {d: sum(1 for s in candidate.sections for m in s.meetings if m.day == d) for d in WEEKDAYS}
    lightest = min((d for d in WEEKDAYS if busy[d]), key=lambda d: busy[d], default=None)
    if lightest:
        examples.append(f"'{lightest}요일 비워줘'")
    if any(m.start < "10:00" for s in candidate.sections for m in s.meetings):
        examples.append("'1교시 피하고 싶어'")
    examples.append("'교양 하나 더 넣어줘'" if candidate.total_credits + 3 <= planner.CREDIT_CAP else f"'{candidate.total_credits - 3:g}학점으로 줄여줘'")
    examples.append(f"'왜 {_key(candidate.sections[0].name)} 넣었어?'")
    if len(chat.candidate_ids) > 1:
        examples.append("'2안 보여줘'")
    return "무엇을 바꿀지 잘 모르겠어. 지금 시간표라면 이렇게 말해 봐: " + ", ".join(examples) + "."


def _select(message: str, chat: PlanChatRequest) -> tuple[str | None, str] | None:
    """'2안으로 바꿔줘' → (후보 id, 답). 해당 없으면 None."""
    found = re.search(r"([1-5])\s*안(?![녕돼되])|([1-5]|첫|두|세|네)\s*번째|([1-5])\s*번\s*후보", message)
    if not found or not re.search(r"바꿔|보여|볼래|골라|선택|로|할래|줘", message):
        return None
    word = next(g for g in found.groups() if g)
    index = {"첫": 1, "두": 2, "세": 3, "네": 4}.get(word) or int(word)
    if not chat.candidate_ids:
        return None, f"화면의 후보 목록을 못 받아서 {index}안으로 못 바꿨어. 위에서 {index}안 탭을 눌러 줘."
    if index > len(chat.candidate_ids):
        return None, f"후보가 {len(chat.candidate_ids)}개뿐이야."
    target = chat.candidate_ids[index - 1]
    picked = planner.store.get(target)
    detail = f" ({len(picked.sections)}과목 {picked.total_credits:g}학점)" if picked else ""
    return target, f"{index}안으로 바꿨어{detail}."


def _why(message: str, candidate: Candidate | None, chat: PlanChatRequest, catalog: list[Course]) -> str | None:
    """'왜 운영체제 넣었어?' → 그 과목의 근거. 해당 없으면 None."""
    if not re.search(r"왜|이유|근거|어째서", message):
        return None
    if candidate is None:
        return "아직 시간표가 없어. 먼저 시간표를 만들어 줘."
    section = next((s for s in candidate.sections if _mentioned(message, s.name)), None)
    if section is None:
        other = next((c for c in catalog if _mentioned(message, c.name)), None)
        if other:
            return f"{other.name}{'은' if _eul(other.name) == '을' else '는'} 지금 시간표에 없어. 넣고 싶으면 '{_key(other.name)} 넣어줘'라고 해 줘."
        return None  # 과목 없이 '왜 이렇게 짰어?' → 전체 설명
    why = section_reasons(section, chat.request, catalog)
    lines = [f"{section.name} ({section.category} {section.credits:g}학점, {section.time_raw}): {', '.join(why) or '학점을 채우면서 다른 과목과 시간이 안 겹쳐서'} 넣었어."]
    rows = prerequisite_check(section.course_code, chat.request.completed, catalog, chat.request.track)
    if rows is None:
        lines.append("선수과목 자료는 아직 없어.")
    elif not rows:
        lines.append("따로 정해진 선수과목은 없어.")
    return "\n".join(lines)


def _explain_response(chat: PlanChatRequest, candidate: Candidate, catalog: list[Course], link: AiLink | None) -> PlanChatResponse:
    facts = explain_facts(candidate, chat.request, None, catalog)
    steps = [
        AgentStep(tool="get_current_timetable", label="후보 분석", detail=f"{len(candidate.sections)}과목 {candidate.total_credits:g}학점"),
        AgentStep(tool="explain", label="근거 정리", detail=f"사실 {len(facts)}개"),
    ]
    reply, mode = "", "rules"
    if link:
        try:
            reply = ai_explain(link, facts)
            mode = "ai"
        except Exception:
            logger.exception("AI 설명 실패. 템플릿으로 설명한다")
    if reply:
        steps.append(AgentStep(tool="explain", label="설명 작성 (AI)", detail="정리한 근거만 사용"))
    else:
        mode, reply = "rules", "\n".join([*facts, EXAMPLES])
        steps.append(AgentStep(tool="explain", label="설명 작성 (템플릿)", detail="정리한 근거 그대로"))
    return PlanChatResponse(reply=reply, applied=False, request=chat.request, steps=steps, mode=mode, previous_candidate_id=candidate.id)


def handle_rules(chat: PlanChatRequest, candidate: Candidate | None, catalog: list[Course], steps: list[AgentStep] | None = None) -> PlanChatResponse:
    steps = list(steps or [])
    previous = candidate.id if candidate else None
    message = chat.message or ""
    base = {"request": chat.request, "mode": "rules", "previous_candidate_id": previous}

    if picked := _select(message, chat):
        target, reply = picked
        steps.append(AgentStep(tool="select_candidate", label="말 이해(규칙): 후보 바꾸기", detail=target or "못 바꿈", ok=target is not None))
        return PlanChatResponse(reply=reply, applied=False, steps=steps, select_candidate=target, **base)
    if (why := _why(message, candidate, chat, catalog)) is not None:
        steps.append(AgentStep(tool="explain", label="말 이해(규칙): 과목 근거 묻기", detail="근거 정리"))
        return PlanChatResponse(reply=why, applied=False, steps=steps, **base)

    edit = parse_rules(message, candidate, catalog)
    understood = describe_edit(edit, catalog)
    steps.append(AgentStep(tool="rules", label="말 이해(규칙)", detail=understood or "알아들은 조건 없음", ok=bool(understood)))
    if not understood:
        if re.search(r"왜|이유|설명|어떻게짰", _compact(message)) and candidate:
            explained = _explain_response(chat, candidate, catalog, None)
            return explained.model_copy(update={"steps": steps[:-1] + explained.steps})
        return PlanChatResponse(reply=suggestions(candidate, chat), applied=False, steps=steps, **base)

    result = rebuild(edit, chat.request, candidate, catalog)
    steps += build_steps(result, "apply_changes")
    if not result.done:
        return PlanChatResponse(reply=". ".join(result.notes) + "." if result.notes else suggestions(candidate, chat), applied=False, steps=steps, **base)
    if not result.ok:
        reason = " ".join(result.response.warnings) or "조건이 너무 빡빡해."
        alts = [a.description for a in result.response.alternatives]
        hint = f" 이렇게 하면 돼: {'; '.join(alts)}." if alts else ""
        return PlanChatResponse(reply=f"{', '.join(result.done)}. 그런데 그러면 맞는 시간표가 없어서 그대로 뒀어. {reason}{hint}", applied=False, steps=steps, **base)
    removed, added = result.diff()
    diff = ([f"빠진 과목: {', '.join(removed)}"] if removed else []) + ([f"새로 들어온 과목: {', '.join(added)}"] if added else [])
    head = ", ".join(result.done) + "." + (" " + ". ".join(result.notes) + "." if result.notes else "")
    reply = "\n".join([head, *diff]) + "\n\n" + explain(result.new, result.request, result.response, catalog)
    return PlanChatResponse(reply=reply, applied=True, request=result.request, response=result.response, steps=steps, mode="rules", previous_candidate_id=previous)


def handle(
    chat: PlanChatRequest,
    catalog: list[Course],
    ask: Callable[..., AiLink | None] = connect,
) -> PlanChatResponse:
    """ask 는 AI 연결을 돌려준다 (테스트는 가짜 클라이언트를, 규칙만 쓰려면 None 을 돌려주는 함수를 넣는다)."""
    candidate = planner.store.get(chat.candidate_id)
    link = ask()
    if not chat.message or not chat.message.strip():
        if candidate is None:
            return PlanChatResponse(reply="아직 설명할 시간표가 없어. 먼저 시간표를 만들어 줘.", applied=False, request=chat.request)
        return _explain_response(chat, candidate, catalog, link)

    steps: list[AgentStep] = []
    if link:
        from app.agent import agent_tools

        try:
            return agent_tools.run(link, chat, candidate, catalog)
        except Exception:
            logger.exception("AI 에이전트 실패. 규칙으로 처리한다")
            steps.append(AgentStep(tool="ai", label="AI 에이전트", detail="응답 실패, 규칙으로 처리", ok=False))
    return handle_rules(chat, candidate, catalog, steps)
