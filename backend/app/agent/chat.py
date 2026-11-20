"""채팅으로 시간표를 고친다.

AI 는 사용자의 말을 이해해 '조건'만 고친다. 시간표는 항상 코드(generate_timetables)가
다시 만들기 때문에, 채팅으로 바꿔도 시간이 겹치거나 없는 과목이 들어가지 않는다.
"""

import json
import re
from collections.abc import Callable

from pydantic import BaseModel, ValidationError

from app.agent import claude
from app.agent.claude import ChatUnavailable  # noqa: F401  (라우터가 여기서 가져간다)
from app.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    Course,
    TimeBlock,
    TimetableRequest,
)
from app.services.course_time import DAYS
from app.services.timetable import generate_timetables

CANDIDATE_LIMIT = 40
HISTORY_LIMIT = 8
_TIME = re.compile(r"^([01]\d|2[0-4]):[0-5]\d$")


# ---------- AI 와 주고받는 형식 ----------
# AI 가 정해진 모양으로만 답하게 하려고, 사전(dict) 없이 목록만 쓰는 형식을 따로 둔다.


class AiTimeBlock(BaseModel):
    day: str  # 요일 한 글자, 모든 요일이면 "매일"
    start: str  # HH:MM
    end: str  # HH:MM


class AiCategoryCredit(BaseModel):
    category: str
    credits: float


class AiConditions(BaseModel):
    min_credits: float
    max_credits: float
    must_include: list[str]
    exclude: list[str]
    completed: list[str]
    blocked_times: list[AiTimeBlock]
    required_credits: list[AiCategoryCredit]
    exclude_full: bool
    preferred_free_days: list[str]


class AiAnswer(BaseModel):
    reply: str
    conditions: AiConditions


INSTRUCTIONS = """너는 대학생의 수강 시간표 조건을 고쳐 주는 도우미다.
사용자의 요청을 반영해 '조건' 전체를 다시 출력한다. 시간표는 네가 짜지 않는다.
네가 고친 조건으로 프로그램이 시간이 겹치지 않는 시간표를 다시 만든다.

규칙
- 사용자가 바꾸라고 하지 않은 조건은 받은 그대로 둔다.
- 과목은 '후보 과목'과 '지금 시간표'에 있는 교과목코드(code)로만 적는다. 목록에 없는 과목을 지어내지 않는다.
- 과목 추가: 그 code 를 must_include 에 넣고 exclude 에서 뺀다.
  지금 시간표 학점에 새 과목 학점을 더한 값이 max_credits 를 넘으면 max_credits 를 그만큼 올린다.
- 과목 빼기: 그 code 를 exclude 에 넣고 must_include 에서 뺀다.
  빼고 난 학점이 min_credits 보다 적어지면 min_credits 를 그만큼 내린다.
- "교양 하나 추가해줘"처럼 과목을 특정하지 않으면, 후보 과목 중 그 교과구분이면서
  지금 시간표에 없는 과목 하나를 골라 추가하고 reply 에 어떤 과목을 골랐는지 말한다.
- "이미 들었어"는 completed 에 넣는다.
- 요일을 반드시 비워 달라고 하면 blocked_times 에 day=그 요일, start="00:00", end="24:00" 을 넣는다.
  "비우면 좋겠다"처럼 희망이면 preferred_free_days 에 넣는다.
- "아침 수업 싫어", "10시 이후만"은 day="매일", start="00:00", end="10:00" 처럼 막을 시간대로 바꾼다.
- 요일은 월 화 수 목 금 토 일 중 한 글자, 시각은 HH:MM 으로 적는다.
- 요청이 모호하거나 후보에서 과목을 찾지 못하면 조건을 그대로 두고 reply 로 되묻는다.
- 시간표와 관계없는 말에는 조건을 그대로 두고 짧게 답한다.

reply 는 한국어 한두 문장으로, 무엇을 바꿨는지만 말한다."""


def ask_model(payload: str, history: list[ChatMessage]) -> AiAnswer:
    """Claude 에 물어 고친 조건을 받는다 (구조화 출력)."""
    response = claude.client().messages.parse(
        model=claude.model_name(),
        max_tokens=4000,
        output_config={"effort": "low"},
        system=INSTRUCTIONS,
        messages=[
            *({"role": item.role, "content": item.content} for item in history),
            {"role": "user", "content": payload},
        ],
        output_format=AiAnswer,
    )
    if response.parsed_output is None:
        raise ValueError("AI 가 정해진 형식으로 답하지 않았습니다.")
    return response.parsed_output


# ---------- 조건 형식 바꾸기 ----------


def to_ai_conditions(request: TimetableRequest) -> AiConditions:
    return AiConditions(
        min_credits=request.min_credits,
        max_credits=request.max_credits,
        must_include=request.must_include,
        exclude=request.exclude,
        completed=request.completed,
        blocked_times=[
            AiTimeBlock(day=block.day or "매일", start=block.start, end=block.end)
            for block in request.blocked_times
        ],
        required_credits=[
            AiCategoryCredit(category=category, credits=credits)
            for category, credits in request.required_credits.items()
        ],
        exclude_full=request.exclude_full,
        preferred_free_days=request.preferred_free_days,
    )


def from_ai_conditions(
    conditions: AiConditions, base: TimetableRequest, courses: list[Course]
) -> tuple[TimetableRequest, list[str]]:
    """AI 가 돌려준 조건을 검사해 TimetableRequest 로 바꾼다.

    개설 강좌에 없는 과목, 형식이 틀린 시간은 버리고 버린 과목 이름을 함께 돌려준다.
    """
    known_codes = {course.course_code for course in courses}
    code_by_name = {course.name: course.course_code for course in courses}
    dropped: list[str] = []

    def codes(items: list[str], keep: frozenset[str] = frozenset()) -> list[str]:
        result: list[str] = []
        for item in items:
            code = item if item in known_codes else code_by_name.get(item)
            if code is None and item in keep:
                code = item  # 원래 조건에 있던 값은 이번 학기에 개설되지 않았어도 그대로 둔다
            if code is None:
                dropped.append(item)
            elif code not in result:
                result.append(code)
        return result

    must_include = codes(conditions.must_include)
    exclude = [code for code in codes(conditions.exclude) if code not in must_include]
    # 이수 과목은 대부분 이번 학기에 열리지 않는 과목이다. 학생이 불러온 목록을 지우지 않는다.
    completed = [
        code
        for code in codes(conditions.completed, keep=frozenset(base.completed))
        if code not in must_include
    ]

    blocked: list[TimeBlock] = []
    for block in conditions.blocked_times:
        if not (_TIME.match(block.start) and _TIME.match(block.end)) or block.start >= block.end:
            continue
        blocked.append(
            TimeBlock(day=block.day if block.day in DAYS else None, start=block.start, end=block.end)
        )

    request = TimetableRequest(
        min_credits=conditions.min_credits,
        max_credits=conditions.max_credits,
        must_include=must_include,
        exclude=exclude,
        completed=completed,
        blocked_times=blocked,
        required_credits={
            item.category: item.credits for item in conditions.required_credits if item.credits > 0
        },
        exclude_full=conditions.exclude_full,
        preferred_free_days=[day for day in conditions.preferred_free_days if day in DAYS],
        max_results=base.max_results,
    )
    return request, dropped


# ---------- AI 에게 보여 줄 과목 고르기 ----------


def _brief(course: Course) -> dict:
    return {
        "code": course.course_code,
        "name": course.name,
        "category": course.category,
        "credits": course.credits,
    }


def _bigrams(text: str) -> set[str]:
    text = re.sub(r"\s+", "", text)
    return {text[index : index + 2] for index in range(len(text) - 1)}


def find_candidates(message: str, courses: list[Course], limit: int = CANDIDATE_LIMIT) -> list[dict]:
    """사용자의 말과 관련 있어 보이는 과목만 추린다 (과목이 수천 개면 전부 보낼 수 없다)."""
    subjects: dict[str, Course] = {}
    for course in courses:
        subjects.setdefault(course.course_code, course)
    if len(subjects) <= limit:
        return [_brief(course) for course in subjects.values()]

    compact = re.sub(r"\s+", "", message)
    wanted = _bigrams(message)
    scored: list[tuple[float, str]] = []
    for code, course in subjects.items():
        name = re.sub(r"\s+", "", course.name)
        score = 0.0
        if name and name in compact or code in message:
            score += 100
        score += len(wanted & _bigrams(name))
        if course.category in message:
            score += 2
        if score > 0:
            scored.append((score, code))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [_brief(subjects[code]) for _, code in scored[:limit]]


# ---------- 채팅 한 번 처리 ----------


def handle_chat(
    chat: ChatRequest,
    courses: list[Course],
    ask: Callable[[str, list[ChatMessage]], AiAnswer] = ask_model,
) -> ChatResponse:
    base = chat.request.model_copy(update={"prefer_courses": []})
    current_ids = set(chat.current_course_ids)
    current = [course for course in courses if course.course_id in current_ids]

    payload = json.dumps(
        {
            "사용자의 말": chat.message,
            "조건": to_ai_conditions(base).model_dump(),
            "지금 시간표": [
                {
                    **_brief(course),
                    "time": ", ".join(f"{m.day} {m.start}~{m.end}" for m in course.meetings),
                }
                for course in current
            ],
            "지금 시간표 학점": sum(course.credits for course in current),
            "후보 과목": find_candidates(chat.message, courses),
        },
        ensure_ascii=False,
    )
    answer = ask(payload, chat.history[-HISTORY_LIMIT:])

    try:
        updated, dropped = from_ai_conditions(answer.conditions, base, courses)
    except ValidationError:
        return ChatResponse(
            reply="요청을 조건으로 바꾸지 못했습니다. 조금 더 구체적으로 말씀해 주세요.",
            applied=False,
            request=base,
        )

    if updated == base:  # 바뀐 조건이 없다 (되묻기, 잡담 등)
        return ChatResponse(reply=answer.reply, applied=False, request=base)

    # 지금 보고 있는 시간표에서 최대한 덜 바뀌도록, 그 강좌들을 유지하는 쪽을 우선한다.
    result = generate_timetables(
        courses, updated.model_copy(update={"prefer_courses": chat.current_course_ids})
    )
    if not result.timetables:
        return ChatResponse(
            reply=f"그렇게 바꾸면 조건에 맞는 시간표가 없어서 적용하지 않았습니다. {result.message}",
            applied=False,
            request=base,
        )

    reply = answer.reply
    if dropped:
        reply += f" (개설 강좌에서 찾지 못해 반영하지 않은 과목: {', '.join(dropped)})"
    return ChatResponse(reply=reply, applied=True, request=updated, result=result)
