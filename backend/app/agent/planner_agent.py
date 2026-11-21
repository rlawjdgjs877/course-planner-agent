"""시간표 에이전트. 시간표를 만든 뒤 붙는 채팅이 이것을 쓴다.

Claude 는 학생의 말을 해석하고, 필요한 도구를 골라 부른 뒤, 결과를 설명한다.
과목 검색, 시간 겹침, 학점 계산, 조합 탐색은 모두 코드(도구)가 한다. 시간표는 항상
planner.generate 가 다시 만들기 때문에, 채팅으로 바꿔도 시간이 겹치거나 없는 과목이 들어가지 않는다.

도구
- search_courses: 이번 학기 개설 강좌 찾기 (과목명·코드·교수·교과구분·요일)
- update_timetable: 조건을 고쳐 지금 시간표를 바탕으로 다시 만들기 (과목 넣기·빼기, 공강, 피할 시간, 학점)
- check_prerequisites: 학과 권장 선후수 순서로 먼저 들을 과목 확인
"""

import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from app.agent import claude
from app.schemas import (
    Candidate,
    ChatMessage,
    Course,
    DayTime,
    GenerateTimetableRequest,
    GenerateTimetableResponse,
)
from app.services import planner, prerequisites

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 6
HISTORY_LIMIT = 10
SEARCH_LIMIT = 12
DAYS = ("월", "화", "수", "목", "금", "토", "일")


# ---------- 요청과 응답 ----------


class AgentStep(BaseModel):
    tool: str = Field(description="부른 도구 이름")
    label: str = Field(description="화면에 보여 줄 한 줄. 예: '과목 검색: 운영체제'")
    ok: bool = True


class AgentChatRequest(BaseModel):
    mode: Literal["chat", "summary"] = Field(
        default="chat", description="summary: 방금 만든 시간표를 요약한다 (message 는 비워도 된다)"
    )
    message: str = Field(default="", max_length=500)
    request: GenerateTimetableRequest = Field(description="지금 시간표를 만든 조건")
    candidate_id: str | None = Field(default=None, description="학생이 지금 보고 있는 후보 (tt_001 등)")
    history: list[ChatMessage] = Field(default_factory=list, description="이전 대화 (최근 것만)")


class AgentChatResponse(BaseModel):
    reply: str
    steps: list[AgentStep] = Field(default_factory=list)
    applied: bool = Field(description="시간표를 새로 만들었는지")
    request: GenerateTimetableRequest = Field(description="적용된 조건 (안 바뀌었으면 보낸 그대로)")
    result: GenerateTimetableResponse | None = Field(default=None, description="새로 만든 시간표")


# ---------- 프롬프트 ----------

SYSTEM = """너는 경북대학교 컴퓨터학부 학생의 2026학년도 2학기 수강 시간표를 함께 짜는 에이전트다.
화면에는 학생이 고른 조건으로 프로그램이 만든 시간표가 있고, 너는 그 옆 채팅창에서 학생과 이야기한다.

할 수 있는 일
- 시간표 설명: 왜 이 과목들이 들어갔는지, 주의할 점(선수과목, 피할 시간과 겹침)은 무엇인지
- 시간표 고치기: 과목 넣기·빼기·분반 바꾸기, 공강 요일, 피할 시간, 학점 조정 → update_timetable
- 과목 찾기: 개설 여부, 분반, 시간, 교수, 교양 영역 → search_courses
- 선수과목 확인 → check_prerequisites

규칙
- 과목의 시간, 학점, 개설 여부, 시간 겹침은 반드시 도구 결과나 아래 '지금 시간표'에 있는 것만 말한다. 지어내지 않는다.
- 학생이 과목 이름을 말하면 먼저 search_courses 로 정확한 과목코드나 강좌번호를 찾은 뒤 update_timetable 에 넣는다.
- 특정 분반으로 바꿀 때는 add_courses 에 새 강좌번호(예: COMP0312-002)를, remove_courses 에 원래 강좌번호를 넣는다.
- "교양 하나 더"처럼 과목을 특정하지 않으면 search_courses 로 후보를 보고, 지금 시간표 빈 시간에 맞는 것을 골라 넣는다.
- "금요일 비워줘"처럼 반드시면 free_days_add, "되도록"이면 preferred_free_days_add 를 쓴다.
- "아침 수업 싫어"는 avoid_times_add 에 월~금 각각 00:00~10:00 처럼 넣는다. 꼭 안 된다고 하면 blocked_times_add.
- update_timetable 결과가 status=infeasible 이면 시간표는 바뀌지 않은 것이다. 이유와 대안을 설명하고 무엇을 풀지 물어본다.
- 선수과목 자료는 학과 전공 소개의 '권장 순서'다. 학칙상 수강 금지가 아니라고 함께 말한다.
- 모호하면 도구를 부르지 말고 짧게 되묻는다.
- 시간표와 관계없는 질문에는 짧게 답하고 시간표 이야기로 돌아온다.

답 형식
- 한국어, 친근한 존댓말. 3~6문장 또는 짧은 목록. 마크다운 표는 쓰지 않는다.
- 시간표를 고쳤으면 무엇이 들어가고 빠졌는지, 학점과 공강이 어떻게 됐는지 먼저 말한다."""

SUMMARY_PROMPT = """방금 프로그램이 만든 시간표(지금 시간표)를 학생에게 처음 소개하면서, 왜 이렇게 짰는지 이유를 설명해 줘.
- 첫 문장: 몇 학점, 공강 요일, 전공·교양 구성을 한 문장으로.
- 이어서 '이렇게 짠 이유'를 2~4가지. 과목마다 붙은 '고른 이유'와 지금 조건(공강, 피할 시간, 학년, 트랙)을 근거로 든다.
  예: 꼭 넣을 과목이라서, 내 트랙 전공필수라서, 내 학년 대상이라서, 비워 달라는 요일을 피하려고, 우선 채울 교양 영역이라서.
- 경고가 있으면 가장 중요한 것 1~2개만 (선수과목 권장 순서, 넣지 못한 필수 과목).
- 마지막에 이렇게 말하면 바로 고칠 수 있다고 예시 하나만 들어 줘.
도구는 부르지 않는다. 6문장 안팎으로."""


# ---------- 도구 정의 ----------


def _nullable(schema: dict) -> dict:
    return {"anyOf": [schema, {"type": "null"}]}


_DAY = {"type": "string", "enum": list(DAYS)}
_TIME_BLOCK = {
    "type": "object",
    "properties": {
        "day": _DAY,
        "start": {"type": "string", "description": "HH:MM"},
        "end": {"type": "string", "description": "HH:MM (24:00 가능)"},
    },
    "required": ["day", "start", "end"],
    "additionalProperties": False,
}
_STRINGS = {"type": "array", "items": {"type": "string"}}

TOOLS: list[dict] = [
    {
        "name": "search_courses",
        "description": (
            "2026-2 개설 강좌를 과목 단위로 찾는다. 과목명 일부·과목코드·교수명(query), 교과구분, 요일, 대상 학년으로 거른다. "
            f"최대 {SEARCH_LIMIT}과목을 돌려주고 과목마다 분반(강좌번호, 시간, 교수)이 붙는다. "
            "이미 이수한 과목과 지금 시간표에 있는 과목은 표시해 준다."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "query": _nullable({"type": "string", "description": "과목명 일부, 과목코드, 교수명. 없으면 null"}),
                "category": _nullable(
                    {"type": "string", "enum": ["전공", "교양"], "description": "전공 계열인지 교양인지"}
                ),
                "area": _nullable(
                    {"type": "string", "description": "교양 영역 일부. 예: 인문, 자연, 소양, 기초"}
                ),
                "day": _nullable(_DAY),
                "grade": _nullable({"type": "integer", "description": "대상 학년 1~4"}),
                "fits_current": {
                    "type": "boolean",
                    "description": "true 면 지금 시간표와 시간이 겹치지 않는 분반만 돌려준다",
                },
            },
            "required": ["query", "category", "area", "day", "grade", "fits_current"],
            "additionalProperties": False,
        },
    },
    {
        "name": "update_timetable",
        "description": (
            "조건을 고쳐 시간표를 다시 만든다. 지금 시간표의 과목은 가능하면 유지한다. "
            "바꿀 것만 채우고 나머지는 빈 목록이나 null 로 둔다. 과목은 과목코드(COMP0312), 강좌번호(COMP0312-002), 과목명 모두 된다. "
            "결과로 새 시간표(과목, 학점, 공강, 경고, 넣지 못한 과목, 대안)를 돌려준다. status=infeasible 이면 화면의 시간표는 그대로다."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "add_courses": {**_STRINGS, "description": "반드시 넣을 과목 추가"},
                "remove_courses": {**_STRINGS, "description": "넣지 않을 과목 추가 (반드시 넣을 목록에서도 뺀다)"},
                "release_courses": {
                    **_STRINGS,
                    "description": "'반드시 넣을 과목'·'넣지 않을 과목' 목록에서 풀어 주기만 할 과목",
                },
                "mark_completed": {**_STRINGS, "description": "학생이 이미 들었다고 한 과목"},
                "free_days_add": {"type": "array", "items": _DAY, "description": "반드시 비울 요일 추가"},
                "free_days_remove": {"type": "array", "items": _DAY, "description": "반드시 비울 요일에서 빼기"},
                "preferred_free_days_add": {
                    "type": "array",
                    "items": _DAY,
                    "description": "가능하면 비울 요일 추가",
                },
                "blocked_times_add": {"type": "array", "items": _TIME_BLOCK, "description": "반드시 비울 시간"},
                "avoid_times_add": {"type": "array", "items": _TIME_BLOCK, "description": "가능하면 피할 시간"},
                "clear_time_preferences": {
                    "type": "boolean",
                    "description": "true 면 기존 '반드시 비울 시간'과 '가능하면 피할 시간'을 모두 지운 뒤 위의 추가분만 적용",
                },
                "min_credits": _nullable({"type": "number"}),
                "target_credits": _nullable({"type": "number"}),
                "max_credits": _nullable({"type": "number"}),
                "ge_areas": _nullable({**_STRINGS, "description": "가능하면 채울 교양 영역 (목록 전체를 바꾼다)"}),
                "prefer_professor": _nullable({**_STRINGS, "description": "선호 교수 (목록 전체를 바꾼다)"}),
            },
            "required": [
                "add_courses", "remove_courses", "release_courses", "mark_completed",
                "free_days_add", "free_days_remove", "preferred_free_days_add",
                "blocked_times_add", "avoid_times_add", "clear_time_preferences",
                "min_credits", "target_credits", "max_credits", "ge_areas", "prefer_professor",
            ],
            "additionalProperties": False,
        },
    },
    {
        "name": "check_prerequisites",
        "description": (
            "학과 전공 소개의 선후수 흐름으로, 과목을 듣기 전에 먼저 들으면 좋은 과목과 학생의 이수 여부를 확인한다. "
            "학칙상 수강 제한이 아니라 권장 순서다."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"courses": {**_STRINGS, "description": "확인할 과목명 또는 과목코드"}},
            "required": ["courses"],
            "additionalProperties": False,
        },
    },
]


# ---------- 도구 실행 ----------


@dataclass
class _State:
    request: GenerateTimetableRequest
    catalog: list[Course]
    candidate: Candidate | None
    result: GenerateTimetableResponse | None = None
    steps: list[AgentStep] = field(default_factory=list)

    @property
    def track_courses(self) -> list[Course]:
        track = self.request.track if self.request.track in planner.TRACKS else None
        return [planner.for_track(course, track) for course in self.catalog]


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def _section_brief(course: Course) -> dict:
    return {
        "강좌번호": course.course_id,
        "시간": ", ".join(f"{m.day} {m.start}~{m.end}" for m in course.meetings) or "미정",
        "교수": course.professor,
    }


def section_reasons(course: Course, request: GenerateTimetableRequest, catalog: list[Course]) -> list[str]:
    """프로그램이 이 분반을 고른 근거. 요청 조건과 과목 정보로만 판단한다 (지어내지 않는다)."""
    reasons: list[str] = []
    if any(_matches_item(item, course.course_id, catalog) for item in request.must_include):
        reasons.append("꼭 넣을 과목으로 고른 과목")
    category = course.category or ""
    track = planner.TRACKS.get(request.track or "")
    if "전공필수" in category:
        reasons.append(f"{track + ' ' if track else ''}전공필수")
    elif "전공" in category:
        reasons.append(f"{track + ' ' if track else ''}전공")
    if course.area:
        preferred = any(area and area in course.area for area in request.ge_areas)
        reasons.append(f"{'우선 채울 ' if preferred else ''}교양 영역({course.area})")
    if request.grade and course.grade:
        if course.grade == str(request.grade):
            reasons.append(f"{request.grade}학년 대상")
        elif course.grade == "*":
            reasons.append("전학년 대상")
    if course.professor and any(p and p in course.professor for p in request.prefer_professor):
        reasons.append("선호 교수 수업")
    return reasons


def candidate_brief(candidate: Candidate, request: GenerateTimetableRequest | None = None, catalog: list[Course] | None = None) -> dict:
    return {
        "id": candidate.id,
        "총학점": candidate.total_credits,
        "공강(월~금)": candidate.free_days,
        "구분별 학점": candidate.credits_by_category,
        "수업 사이 빈 시간(분)": candidate.gap_minutes,
        "과목": [
            {
                "과목": s.name,
                "강좌번호": s.course_id,
                "학점": s.credits,
                "구분": s.category,
                **({"교양 영역": s.area} if s.area else {}),
                **({"대상 학년": s.grade} if s.grade else {}),
                "시간": ", ".join(f"{m.day} {m.start}~{m.end}" for m in s.meetings) or "미정",
                "교수": s.professor,
                **({"고른 이유": section_reasons(s, request, catalog or [])} if request is not None else {}),
            }
            for s in candidate.sections
        ],
        "경고": candidate.warnings,
    }


def _conflicts(course: Course, taken: list[Course]) -> bool:
    for other in taken:
        if other.course_code == course.course_code:
            continue
        for a in course.meetings:
            for b in other.meetings:
                if a.day == b.day and a.start < b.end and b.start < a.end:
                    return True
    return False


def search_courses(state: _State, args: dict) -> dict:
    query = _norm(args.get("query") or "")
    category, area, day, grade = args.get("category"), args.get("area"), args.get("day"), args.get("grade")
    current = state.candidate.sections if state.candidate else []
    current_codes = {c.course_code for c in current}
    completed = set(state.request.completed)
    subjects: dict[str, list[Course]] = {}
    for course in state.track_courses:
        if planner.not_recommended(course):
            continue
        if query and query not in _norm(f"{course.name}{course.course_code}{course.course_id}{course.professor or ''}"):
            continue
        if category == "교양" and course.category != "교양" and not course.area:
            continue
        if category == "전공" and (course.category == "교양" or course.area):
            continue
        if area and area not in (course.area or ""):
            continue
        if day and not any(m.day == day for m in course.meetings):
            continue
        if grade and course.grade not in (str(grade), "*"):
            continue
        if args.get("fits_current") and _conflicts(course, current):
            continue
        subjects.setdefault(course.course_code, []).append(course)

    def rank(code: str) -> tuple:
        first = subjects[code][0]
        exact = query and _norm(first.name) == query
        return (not exact, code in completed, len(first.name))

    codes = sorted(subjects, key=rank)
    found = []
    for code in codes[:SEARCH_LIMIT]:
        first = subjects[code][0]
        found.append(
            {
                "과목": first.name,
                "과목코드": code,
                "학점": first.credits,
                "구분": first.category,
                **({"교양 영역": first.area} if first.area else {}),
                **({"대상 학년": first.grade} if first.grade else {}),
                **({"이미 이수": True} if code in completed else {}),
                **({"지금 시간표에 있음": True} if code in current_codes else {}),
                "분반": [_section_brief(c) for c in subjects[code][:6]],
            }
        )
    label = args.get("query") or area or category or "조건"
    state.steps.append(AgentStep(tool="search_courses", label=f"과목 검색: {label} ({len(codes)}개)"))
    return {"찾은 과목 수": len(codes), "과목": found, **({"안내": "더 있으니 조건을 좁혀 보세요"} if len(codes) > SEARCH_LIMIT else {})}


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item.strip() for item in items if item and item.strip()))


def _matches_item(item: str, target: str, catalog: list[Course]) -> bool:
    """item 과 target 이 같은 과목을 가리키는지 (코드, 강좌번호, 이름 중 무엇으로 적었든)."""
    if item == target:
        return True
    a = {c.course_code for c in planner._matches(item, catalog)}
    b = {c.course_code for c in planner._matches(target, catalog)}
    return bool(a & b) and ("-" not in item or "-" not in target)


def apply_changes(base: GenerateTimetableRequest, args: dict, catalog: list[Course]) -> GenerateTimetableRequest:
    data = base.model_dump()
    add, remove = _unique(args.get("add_courses", [])), _unique(args.get("remove_courses", []))
    release = _unique(args.get("release_courses", []))

    def without(items: list[str], drop: list[str]) -> list[str]:
        return [item for item in items if not any(_matches_item(item, d, catalog) for d in drop)]

    data["must_include"] = _unique(without(data["must_include"], remove + release) + add)
    data["exclude"] = _unique(without(data["exclude"], add + release) + remove)
    data["completed"] = _unique(data["completed"] + args.get("mark_completed", []))
    data["must_include"] = without(data["must_include"], args.get("mark_completed", []))

    free = [d for d in data["free_days"] if d not in args.get("free_days_remove", [])]
    data["free_days"] = list(dict.fromkeys(free + args.get("free_days_add", [])))
    if args.get("clear_time_preferences"):
        data["blocked_times"], data["avoid_times"] = [], []
    data["blocked_times"] += args.get("blocked_times_add", [])
    preferred = [{"day": d, "start": "00:00", "end": "24:00"} for d in args.get("preferred_free_days_add", [])]
    data["avoid_times"] += args.get("avoid_times_add", []) + preferred
    for key in ("blocked_times", "avoid_times"):
        seen: dict[tuple, dict] = {}
        for block in data[key]:
            seen.setdefault((block["day"], block["start"], block["end"]), block)
        data[key] = list(seen.values())

    for key in ("min_credits", "target_credits", "max_credits"):
        if args.get(key) is not None:
            data[key] = max(0.0, min(30.0, float(args[key])))
    # 하나만 바꿔도 최소 ≤ 목표 ≤ 최대 가 되도록 나머지를 맞춘다
    if args.get("target_credits") is not None:
        data["min_credits"] = min(data["min_credits"], data["target_credits"])
        data["max_credits"] = max(data["max_credits"], data["target_credits"])
    if args.get("min_credits") is not None:
        data["target_credits"] = max(data["target_credits"], data["min_credits"])
        data["max_credits"] = max(data["max_credits"], data["target_credits"])
    if args.get("max_credits") is not None:
        data["target_credits"] = min(data["target_credits"], data["max_credits"])
        data["min_credits"] = min(data["min_credits"], data["target_credits"])
    for key in ("ge_areas", "prefer_professor"):
        if args.get(key) is not None:
            data[key] = _unique(args[key])
    return GenerateTimetableRequest.model_validate(data)


def _describe_changes(args: dict) -> str:
    parts = []
    if args.get("add_courses"):
        parts.append("넣기 " + ", ".join(args["add_courses"]))
    if args.get("remove_courses"):
        parts.append("빼기 " + ", ".join(args["remove_courses"]))
    if args.get("free_days_add"):
        parts.append("공강 " + "·".join(args["free_days_add"]))
    if args.get("preferred_free_days_add"):
        parts.append("되도록 공강 " + "·".join(args["preferred_free_days_add"]))
    if args.get("blocked_times_add") or args.get("avoid_times_add"):
        parts.append("시간 조건")
    if any(args.get(k) is not None for k in ("min_credits", "target_credits", "max_credits")):
        parts.append("학점")
    return ", ".join(parts) or "조건 변경"


def update_timetable(state: _State, args: dict) -> dict:
    label = f"시간표 다시 만들기: {_describe_changes(args)}"
    try:
        updated = apply_changes(state.request, args, state.catalog)
    except ValidationError as error:
        state.steps.append(AgentStep(tool="update_timetable", label=label, ok=False))
        return {"오류": "조건이 올바르지 않습니다", "자세히": [e["msg"] for e in error.errors()][:3]}

    base_id = state.candidate.id if state.candidate else None
    result = planner.generate(updated.model_copy(update={"base_candidate_id": base_id}), state.catalog)
    if not result.candidates:
        state.steps.append(AgentStep(tool="update_timetable", label=label, ok=False))
        return {
            "status": "infeasible",
            "설명": "이 조건으로는 시간표를 만들 수 없어 화면의 시간표를 바꾸지 않았습니다.",
            "경고": result.warnings,
            "넣지 못한 과목": [o.model_dump(exclude_none=True) for o in result.omitted_required],
            "대안": [{"설명": a.description, "풀어 준 조건": a.relaxed} for a in result.alternatives],
        }

    before = {s.course_id: s.name for s in state.candidate.sections} if state.candidate else {}
    new = result.candidates[0]
    after = {s.course_id: s.name for s in new.sections}
    state.request, state.result, state.candidate = updated, result, new
    state.steps.append(AgentStep(tool="update_timetable", label=label))
    return {
        "status": result.status,
        "새 시간표": candidate_brief(new),
        "들어간 과목": [after[i] for i in after if i not in before],
        "빠진 과목": [before[i] for i in before if i not in after],
        "넣지 못한 필수 과목": [o.model_dump(exclude_none=True) for o in result.omitted_required],
        "전체 경고": result.warnings,
        "대안": [{"설명": a.description} for a in result.alternatives],
    }


def check_prerequisites(state: _State, args: dict) -> dict:
    completed_codes = set(state.request.completed)
    completed = {prerequisites.normalize(n) for n in [*state.request.completed_names, *state.request.completed]}
    completed |= {prerequisites.normalize(c.name) for c in state.catalog if c.course_code in completed_codes}
    answers = []
    for item in _unique(args.get("courses", []))[:10]:
        found = planner._matches(item, state.catalog)
        name = found[0].name if found else item
        stages = prerequisites.requirements_of(name)
        answers.append(
            {
                "과목": name,
                "먼저 들으면 좋은 과목": [prerequisites.display(s) for s in stages] or "자료에 없음",
                "이수 기록 없음": [prerequisites.display(s) for s in prerequisites.missing(name, completed)],
            }
        )
    state.steps.append(AgentStep(tool="check_prerequisites", label="선수과목 확인: " + ", ".join(a["과목"] for a in answers)))
    return {
        "결과": answers,
        "참고": "학과 전공 소개의 권장 순서입니다. 학칙상 수강 제한은 아닙니다."
        + ("" if completed_codes or state.request.completed_names else " 학생이 이수 과목을 입력하지 않았습니다."),
    }


HANDLERS: dict[str, Callable[[_State, dict], dict]] = {
    "search_courses": search_courses,
    "update_timetable": update_timetable,
    "check_prerequisites": check_prerequisites,
}


# ---------- 대화 한 번 ----------


def _context(state: _State) -> str:
    request = state.request
    conditions = {
        "학점(최소/목표/최대)": [request.min_credits, request.target_credits, request.max_credits],
        "반드시 공강": request.free_days,
        "반드시 비울 시간": [b.model_dump() for b in request.blocked_times],
        "가능하면 피할 시간": [b.model_dump() for b in request.avoid_times],
        "반드시 넣을 과목": request.must_include,
        "넣지 않을 과목": request.exclude,
        "우선 교양 영역": request.ge_areas,
        "트랙": planner.TRACKS.get(request.track or "", "모름"),
        "학년": request.grade or "모름",
        "이수 과목 수": len(request.completed),
    }
    return json.dumps(
        {
            "지금 조건": conditions,
            "지금 시간표": candidate_brief(state.candidate, request, state.catalog) if state.candidate else "아직 없음",
        },
        ensure_ascii=False,
    )


def fallback_summary(candidate: Candidate, request: GenerateTimetableRequest, catalog: list[Course]) -> str:
    """AI 를 쓸 수 없을 때 보여 줄 요약. 프로그램이 아는 근거만 문장으로 옮긴다."""
    majors = sum(v for k, v in candidate.credits_by_category.items() if "전공" in k)
    lines = [
        f"{candidate.total_credits:g}학점짜리 시간표예요."
        + (f" {', '.join(candidate.free_days)}요일은 공강이에요." if candidate.free_days else "")
        + (f" 전공 {majors:g}학점, 그 밖에 {candidate.total_credits - majors:g}학점이에요." if majors else "")
    ]
    reasons = []
    for s in candidate.sections:
        why = section_reasons(s, request, catalog)
        if why:
            reasons.append(f"{s.name}: {', '.join(why)}")
    if reasons:
        lines.append("이렇게 고른 이유예요. " + " / ".join(reasons[:6]))
    if request.free_days:
        lines.append(f"반드시 비워 달라고 한 {', '.join(request.free_days)}요일에는 수업을 넣지 않았어요.")
    if candidate.warnings:
        lines.append("확인할 점: " + candidate.warnings[0])
    lines.append("AI 연결이 아직 안 돼서 대화로 고치기는 쓸 수 없어요. backend/.env 에 ANTHROPIC_API_KEY 를 넣으면 \"금요일 비워줘\"처럼 말해서 바로 고칠 수 있어요.")
    return "\n".join(lines)


Ask = Callable[[list[dict]], Any]


def ask_claude(messages: list[dict]):
    return claude.client().messages.create(
        model=claude.model_name(),
        max_tokens=8000,
        output_config={"effort": "low"},
        system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        tools=TOOLS,
        messages=messages,
    )


def fallback_response(chat: AgentChatRequest, catalog: list[Course]) -> AgentChatResponse | None:
    candidate = planner.store.get(chat.candidate_id)
    if candidate is None:
        return None
    request = chat.request.model_copy(update={"base_candidate_id": None})
    return AgentChatResponse(reply=fallback_summary(candidate, request, catalog), applied=False, request=request)


def handle(chat: AgentChatRequest, catalog: list[Course], ask: Ask = ask_claude) -> AgentChatResponse:
    candidate = planner.store.get(chat.candidate_id)
    state = _State(request=chat.request.model_copy(update={"base_candidate_id": None}), catalog=catalog, candidate=candidate)

    if chat.mode == "summary":
        if candidate is None:
            return AgentChatResponse(
                reply="요약할 시간표를 찾지 못했어요. 시간표를 다시 만들어 주세요.", applied=False, request=state.request
            )
        user_text = SUMMARY_PROMPT
    else:
        if not chat.message.strip():
            return AgentChatResponse(reply="무엇을 도와드릴까요?", applied=False, request=state.request)
        user_text = chat.message.strip()

    messages: list[dict] = [{"role": m.role, "content": m.content} for m in chat.history[-HISTORY_LIMIT:]]
    while messages and messages[0]["role"] != "user":
        messages.pop(0)
    messages.append({"role": "user", "content": f"<화면 상태>\n{_context(state)}\n</화면 상태>\n\n{user_text}"})

    reply = ""
    for _ in range(MAX_TOOL_ROUNDS):
        response = ask(messages)
        texts = [b.text for b in response.content if b.type == "text"]
        if response.stop_reason == "refusal":
            reply = "이 요청은 도와드리기 어려워요. 시간표에 관한 다른 걸 물어봐 주세요."
            break
        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if not tool_uses:
            reply = "\n".join(t for t in texts if t.strip())
            break
        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in tool_uses:
            handler = HANDLERS.get(block.name)
            try:
                if handler is None:
                    raise ValueError(f"없는 도구: {block.name}")
                output = handler(state, dict(block.input))
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(output, ensure_ascii=False)})
            except Exception as error:  # 도구 하나가 실패해도 대화는 이어 간다
                logger.exception("agent tool failed")
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": f"오류: {error}", "is_error": True})
        messages.append({"role": "user", "content": results})
    else:
        reply = "요청을 처리하는 데 단계가 너무 많이 필요했어요. 조금 더 나눠서 말씀해 주세요."

    return AgentChatResponse(
        reply=reply or "처리했어요.",
        steps=state.steps,
        applied=state.result is not None,
        request=state.request,
        result=state.result,
    )
