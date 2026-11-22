"""'나의 시간표' AI 에이전트의 도구와 루프.

OpenAI Chat Completions 의 function calling 으로 최대 MAX_STEPS 번 도구를 부른다.
도구는 모두 코드다: 과목 검색은 카탈로그에서, 시간표는 planner.generate 가 만들고 검증한다.
AI 는 어떤 도구를 부를지 정하고, 도구 결과만 근거로 답한다.
"""

import json
import logging
import re
from typing import Any

from app.agent.chat import find_candidates
from app.agent.plan_chat import (
    HISTORY_LIMIT,
    AgentStep,
    AiLink,
    Edit,
    PlanChatRequest,
    PlanChatResponse,
    Rebuild,
    _key,
    build_steps,
    prerequisite_check,
    prerequisite_items,
    rebuild,
    section_reasons,
    summarize,
    verify_step,
)
from app.schemas import Candidate, Course
from app.services import planner

logger = logging.getLogger(__name__)

MAX_STEPS = 5
SEARCH_LIMIT = 10

SYSTEM = """너는 대학생의 '나의 시간표'를 고쳐 주는 AI 에이전트다. 도구를 써서 일한다.
- 시간표 조합과 검증은 apply_changes 도구(프로그램)가 한다. 너는 시간표를 직접 짜지 않는다.
- 과목은 search_courses 나 get_current_timetable 결과에 나온 code 로만 다룬다. 과목·시간·학점을 지어내지 않는다.
- 과목을 넣기 전, 필요하면 check_prerequisites 로 선수과목을 확인한다.
- 조건을 바꿔야 하면 apply_changes 를 부른다. 결과가 ok=false 면 notes·alternatives 를 보고 다른 방법을 한 번 더 시도하거나 학생에게 설명한다.
- 'N안 보여줘' 같은 말은 select_candidate 를 부른다.
- '왜 ○○ 넣었어' 같은 질문은 get_current_timetable 의 reasons 와 check_prerequisites 결과만 근거로 답한다.
- 모호하면 도구를 부르지 말고 짧게 되묻는다.
마지막 답은 한국어 반말 2~4문장. 도구 결과에 있는 사실(바뀐 과목, 학점, 경고, 대안)만 말한다."""

_EDIT_PROPS = {
    "add": {"type": "array", "items": {"type": "string"}, "description": "넣을 과목 code"},
    "remove": {"type": "array", "items": {"type": "string"}, "description": "뺄 과목 code"},
    "add_category": {"type": "string", "description": "이 구분(교양 또는 전공) 과목 하나를 프로그램이 골라 넣는다"},
    "remove_category": {"type": "string", "description": "지금 시간표에서 이 구분(교양 또는 전공) 과목 하나를 뺀다"},
    "free_days": {"type": "array", "items": {"type": "string"}, "description": "반드시 비울 요일 한 글자 (월~토)"},
    "unfree_days": {"type": "array", "items": {"type": "string"}, "description": "공강을 풀 요일"},
    "allow_weekend": {"type": "boolean", "description": "주말 수업도 넣어도 되는지"},
    "no_class_before": {"type": "integer", "description": "평일 이 시각(1~23) 전에는 수업 없음. 아침 수업 싫어=10"},
    "no_class_after": {"type": "integer", "description": "평일 이 시각(1~23) 뒤에는 수업 없음"},
    "target_credits": {"type": "number", "description": "목표 학점"},
    "credits_delta": {"type": "number", "description": "지금 학점에서 늘리거나(+) 줄일(-) 학점"},
}


def _tool(name: str, description: str, properties: dict, required: list[str] | None = None) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties, "required": required or []},
        },
    }


TOOLS = [
    _tool("search_courses", "개설 강좌에서 과목명이나 과목코드로 과목을 찾는다 (최대 10개, 시간·학점 포함).",
          {"query": {"type": "string"}, "category": {"type": "string", "description": "교양, 전공필수, 전공선택 등"}}, ["query"]),
    _tool("check_prerequisites", "과목의 선수과목과 학생의 이수 여부를 확인한다.", {"course": {"type": "string", "description": "과목명이나 code"}}, ["course"]),
    _tool("apply_changes", "조건을 바꿔 프로그램이 시간표를 실제로 다시 만들고 검증한다. 여러 번 부를 수 있고 앞선 변경 위에 쌓인다.", _EDIT_PROPS),
    _tool("get_current_timetable", "지금 시간표(과목, 시간, 학점, 과목별 넣은 이유)를 본다.", {}),
    _tool("select_candidate", "화면의 N번째 후보(N안)를 보여 준다.", {"index": {"type": "integer", "description": "1부터"}}, ["index"]),
]


class Toolbox:
    """도구 실행과 상태. apply_changes 가 성공할 때마다 그 결과 위에 다음 변경을 쌓는다."""

    def __init__(self, chat: PlanChatRequest, candidate: Candidate | None, catalog: list[Course]) -> None:
        self.chat = chat
        self.catalog = catalog
        self.request = chat.request
        self.candidate = candidate
        self.last: Rebuild | None = None  # 마지막 성공
        self.done: list[str] = []
        self.selected: str | None = None
        self.steps: list[AgentStep] = []

    def run(self, name: str, arguments: str) -> dict:
        try:
            args = json.loads(arguments or "{}")
        except json.JSONDecodeError:
            args = {}
        handler = getattr(self, f"tool_{name}", None)
        if handler is None:
            self.steps.append(AgentStep(tool=name, label=f"알 수 없는 도구: {name}", ok=False))
            return {"error": "그런 도구는 없어"}
        try:
            return handler(**args) if isinstance(args, dict) else handler()
        except TypeError as error:
            self.steps.append(AgentStep(tool=name, label=f"{name} 호출 오류", detail=str(error)[:80], ok=False))
            return {"error": f"인자가 잘못됐어: {error}"}

    # ----- 도구들 -----

    def tool_search_courses(self, query: str = "", category: str | None = None) -> dict:
        track = planner.resolve_track(self.request.track)
        key = _key(query)
        by_code: dict[str, list[Course]] = {}
        for course in self.catalog:
            by_code.setdefault(course.course_code, []).append(planner.for_track(course, track))
        hits = [code for code, sections in by_code.items() if key and (key in _key(sections[0].name) or query.strip().upper() == code)]
        if not hits:
            hits = [item["code"] for item in find_candidates(query, self.catalog, SEARCH_LIMIT * 3) if re.search(r"\S", query)]
        if category:
            hits = [code for code in hits if category in (by_code[code][0].category or "")]
        hits = hits[:SEARCH_LIMIT]
        current = {s.course_code for s in self.candidate.sections} if self.candidate else set()
        found = [
            {
                "code": code,
                "name": by_code[code][0].name,
                "category": by_code[code][0].category,
                "credits": by_code[code][0].credits,
                "grade": by_code[code][0].grade,
                "in_timetable": code in current,
                "sections": [{"id": s.course_id, "time": s.time_raw, "professor": s.professor} for s in by_code[code][:4]],
            }
            for code in hits
        ]
        self.steps.append(AgentStep(tool="search_courses", label=f"과목 검색: {query}" + (f" ({category})" if category else ""), detail=f"{len(found)}개 찾음", ok=bool(found)))
        return {"courses": found}

    def tool_check_prerequisites(self, course: str = "") -> dict:
        rows = prerequisite_check(course, self.request.completed, self.catalog, self.request.track)
        if rows is None:
            self.steps.append(AgentStep(tool="check_prerequisites", label=f"선수과목 확인: {course}", detail="데이터 없음", ok=False))
            return {"available": False, "message": "선수과목 데이터 없음. 선수과목 이야기는 하지 마."}
        items = prerequisite_items(rows)
        done = sum(1 for _, ok in items if ok)
        detail = f"선수과목 {len(items)}개 중 {done}개 이수" if items else "선수과목 없음"
        self.steps.append(AgentStep(tool="check_prerequisites", label=f"선수과목 확인: {course}", detail=detail))
        return {
            "available": True,
            "completed": self.request.completed,
            "completed_known": bool(self.request.completed),
            "prerequisites": rows,  # [{chain, required(바로 앞 단계), satisfied, page}]. 빈 목록이면 확인할 선수과목 없음
            "note": "권장 이수 순서 기준이고 학칙상 수강 제한은 아니다. completed_known 이 false 면 미이수라고 단정하지 마.",
        }

    def tool_apply_changes(self, **fields: Any) -> dict:
        edit = Edit(**{k: v for k, v in fields.items() if k in _EDIT_PROPS and v is not None})
        result = rebuild(edit, self.request, self.candidate, self.catalog)
        self.steps += build_steps(result, "apply_changes")
        if result.ok:
            self.last = result
            self.request = result.request
            self.candidate = result.new
            self.done += result.done
        return result.summary()

    def tool_get_current_timetable(self) -> dict:
        summary = summarize(self.candidate)
        if summary is None:
            self.steps.append(AgentStep(tool="get_current_timetable", label="지금 시간표 확인", detail="시간표 없음", ok=False))
            return {"timetable": None}
        for item, section in zip(summary["sections"], self.candidate.sections):
            item["reasons"] = section_reasons(section, self.request, self.catalog)
        summary["target_credits"] = self.request.target_credits
        summary["free_days_requested"] = self.request.free_days
        self.steps.append(AgentStep(tool="get_current_timetable", label="지금 시간표 확인", detail=f"{len(summary['sections'])}과목 {summary['total_credits']:g}학점"))
        return {"timetable": summary}

    def tool_select_candidate(self, index: int = 1) -> dict:
        ids = self.chat.candidate_ids
        if not 1 <= index <= len(ids):
            self.steps.append(AgentStep(tool="select_candidate", label=f"{index}안 보기", detail="그런 후보 없음", ok=False))
            return {"ok": False, "candidates": len(ids)}
        self.selected = ids[index - 1]
        self.steps.append(AgentStep(tool="select_candidate", label=f"{index}안 보기", detail=self.selected))
        return {"ok": True, "timetable": summarize(planner.store.get(self.selected))}


def _context(candidate: Candidate | None, chat: PlanChatRequest) -> str:
    if candidate is None:
        return "지금 시간표: 없음"
    names = ", ".join(f"{s.name}({s.course_code})" for s in candidate.sections)
    return f"지금 시간표: {names} / {candidate.total_credits:g}학점 / 화면의 후보 {len(chat.candidate_ids) or 1}개"


def run(link: AiLink, chat: PlanChatRequest, candidate: Candidate | None, catalog: list[Course]) -> PlanChatResponse:
    """도구 루프. 마지막 assistant 메시지가 답이고, 마지막으로 성공한 apply_changes 결과가 시간표다."""
    client, model = link
    box = Toolbox(chat, candidate, catalog)
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM + "\n\n" + _context(candidate, chat)},
        *({"role": m.role, "content": m.content} for m in chat.history[-HISTORY_LIMIT:]),
        {"role": "user", "content": chat.message or ""},
    ]
    reply = ""
    for turn in range(MAX_STEPS + 1):
        last_turn = turn == MAX_STEPS  # 도구를 다 썼으면 답만 하게 한다
        answer = client.chat.completions.create(
            model=model, messages=messages, tools=TOOLS, tool_choice="none" if last_turn else "auto"
        )
        message = answer.choices[0].message
        calls = list(getattr(message, "tool_calls", None) or [])
        if not calls or last_turn:
            reply = (message.content or "").strip()
            break
        messages.append({
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in calls],
        })
        for call in calls:
            result = box.run(call.function.name, call.function.arguments)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result, ensure_ascii=False)})

    last = box.last
    if not reply:  # 답이 비면 코드가 사실만으로 답한다
        reply = ", ".join(box.done) + "." if box.done else "무엇을 바꿀지 잘 모르겠어. 조금만 더 구체적으로 말해 줘."
    steps = list(box.steps)
    if last and last.new and not any(s.tool == "verify" for s in steps[-1:]):
        steps.append(verify_step(last.new, last.request))
    steps.append(AgentStep(tool="reply", label="답 정리 (AI)", detail="도구 결과만 근거로"))
    return PlanChatResponse(
        reply=reply,
        applied=last is not None,
        request=last.request if last else chat.request,
        response=last.response if last else None,
        steps=steps,
        mode="ai",
        previous_candidate_id=candidate.id if candidate else None,
        select_candidate=box.selected if last is None else None,
    )

