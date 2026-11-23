"""'나의 시간표' 화면의 챗봇.

1. 시간표가 만들어지면 왜 이렇게 짰는지 설명한다 (코드가 결과를 보고 설명한다. AI 가 지어내지 않는다).
2. 학생이 말하면 조건만 고치고, 시간표는 planner.generate 가 다시 만든다.
   - OPENAI_API_KEY 와 OPENAI_MODEL 이 있으면 AI 가 말을 '수정 내용'으로 바꾼다.
   - 없으면 자주 쓰는 말(빼줘, 넣어줘, 금요일 비워줘, 아침 수업 싫어, 18학점)을 규칙으로 알아듣는다.
"""

import os
import re
from collections.abc import Callable

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from app.agent.chat import find_candidates
from app.schemas import (
    Candidate,
    ChatMessage,
    Course,
    DayTime,
    GenerateTimetableRequest,
    GenerateTimetableResponse,
)
from app.services import planner

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
    history: list[ChatMessage] = Field(default_factory=list)


class PlanChatResponse(BaseModel):
    reply: str
    applied: bool = Field(description="조건이 바뀌어 시간표를 다시 만들었는지")
    request: GenerateTimetableRequest = Field(description="적용된 조건 (바뀌지 않았으면 보낸 그대로)")
    response: GenerateTimetableResponse | None = Field(default=None, description="다시 만든 시간표")


class Edit(BaseModel):
    """말 한마디를 조건 수정으로 바꾼 것. AI 와 규칙이 같은 모양을 쓴다."""

    reply: str = Field(default="", description="학생에게 할 짧은 답 (무엇을 바꿨는지)")
    add: list[str] = Field(default_factory=list, description="넣을 과목 (과목코드나 과목명)")
    remove: list[str] = Field(default_factory=list, description="뺄 과목 (과목코드나 과목명)")
    free_days: list[str] = Field(default_factory=list, description="반드시 비울 요일 (한 글자)")
    unfree_days: list[str] = Field(default_factory=list, description="공강을 풀 요일")
    no_class_before: int | None = Field(default=None, description="평일 이 시각(0~23) 전에는 수업 없음")
    no_class_after: int | None = Field(default=None, description="평일 이 시각(1~24) 뒤에는 수업 없음")
    target_credits: float | None = Field(default=None, description="목표 학점")
    credits_delta: float | None = Field(default=None, description="지금 학점에서 늘리거나(+) 줄일(-) 학점")


# ---------- 설명 ----------


def explain(candidate: Candidate, request: GenerateTimetableRequest, response: GenerateTimetableResponse | None = None) -> str:
    track = planner.TRACKS.get(request.track or "")
    lines = [f"이 시간표는 {len(candidate.sections)}과목 {candidate.total_credits:g}학점이야 (목표 {request.target_credits:g}학점)."]
    must = {code for item in request.must_include for code in (item, item.split("-")[0])}
    for section in candidate.sections:
        why = []
        if section.course_id in must or section.course_code in must or section.name in must:
            why.append("네가 꼭 넣어 달라고 한 과목")
        sources = {listing.source for listing in section.listings}
        if section.category != "교양" and (request.track in sources or "computing" in sources):
            why.append(f"{track + ' ' if track else '컴학 '}{section.category} 과목")
        elif section.area:
            why.append(f"교양 {section.area}" + (" (희망 영역)" if section.area in request.ge_areas else ""))
        if request.grade and section.grade == str(request.grade):
            why.append(f"{request.grade}학년 대상")
        if section.professor and section.professor in request.prefer_professor:
            why.append("선호 교수")
        lines.append(f"• {section.name}: {', '.join(why) or '학점을 채우면서 다른 과목과 시간이 안 겹쳐서'}")
    if request.free_days:
        lines.append(f"{'·'.join(request.free_days)}요일은 비워 달라고 해서 수업을 안 넣었어.")
    if candidate.free_days:
        lines.append(f"평일 공강: {'·'.join(candidate.free_days)}요일.")
    lines.append(f"수업 사이 빈 시간은 합쳐서 {candidate.gap_minutes / 60:.1f}시간으로 줄이려고 했어.")
    if response:
        for omitted in response.omitted_required:
            lines.append(f"못 넣은 과목: {omitted.name or omitted.item} ({REASONS.get(omitted.reason, omitted.reason)}).")
    lines.append("바꾸고 싶은 게 있으면 말해 줘. 예: '○○ 빼줘', '금요일 비워줘', '아침 수업 싫어', '15학점으로'.")
    return "\n".join(lines)


# ---------- 말 알아듣기 ----------


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _days(text: str) -> list[str]:
    return [day for day in "월화수목금토" if re.search(fr"{day}(요일|욜)", text)]


def parse_rules(message: str, candidate: Candidate | None, catalog: list[Course]) -> Edit:
    """AI 없이 알아듣는 말. 못 알아들으면 빈 Edit 을 돌려준다."""
    text = _compact(message)
    edit = Edit()
    current = {section.name: section.course_code for section in (candidate.sections if candidate else [])}
    if re.search(r"빼|제외|지워|없애|싫", text):
        edit.remove = [code for name, code in current.items() if _compact(name) in text]
    if re.search(r"추가|넣어|넣고|담아|듣고싶|들을래", text):
        names = sorted({c.name for c in catalog if c.name not in current and len(_compact(c.name)) >= 2 and _compact(c.name) in text}, key=len, reverse=True)
        edit.add = names[:1]
    days = _days(text)
    if days and re.search(r"풀|있어도|넣어도|괜찮", text):
        edit.unfree_days = days
    elif days and re.search(r"비워|공강|없|쉬|빼", text):
        edit.free_days = days
    if hour := re.search(r"(\d{1,2})시(이전|전)", text):
        edit.no_class_before = int(hour.group(1))
    elif re.search(r"아침|오전|1교시", text):
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


def ask_model(message: str, candidate: Candidate | None, catalog: list[Course], history: list[ChatMessage]) -> Edit | None:
    """키가 있으면 AI 에게 말을 Edit 으로 바꾸게 한다. 키가 없으면 None."""
    load_dotenv()
    model = os.getenv("OPENAI_MODEL")
    if not (os.getenv("OPENAI_API_KEY") and model):
        return None
    from openai import OpenAI

    current = [{"code": s.course_code, "name": s.name, "credits": s.credits, "time": s.time_raw} for s in (candidate.sections if candidate else [])]
    instructions = (
        "너는 대학생 시간표를 고쳐 주는 도우미다. 학생의 말을 수정 내용(Edit)으로만 바꾼다. 시간표는 프로그램이 다시 짠다.\n"
        "과목은 '지금 시간표'나 '후보 과목'에 있는 code 로만 적고 지어내지 않는다. 바꿀 게 없거나 모호하면 다른 칸은 비우고 reply 로 되묻는다.\n"
        "'금요일 비워줘'는 free_days, '아침 수업 싫어'는 no_class_before=10 처럼 적는다. reply 는 한국어 반말 한두 문장."
    )
    payload = {"학생의 말": message, "지금 시간표": current, "후보 과목": find_candidates(message, catalog)}
    response = OpenAI().responses.parse(
        model=model,
        instructions=instructions,
        input=[*({"role": m.role, "content": m.content} for m in history[-HISTORY_LIMIT:]), {"role": "user", "content": str(payload)}],
        text_format=Edit,
    )
    return response.output_parsed


def apply(edit: Edit, request: GenerateTimetableRequest, candidate: Candidate | None, catalog: list[Course]) -> tuple[GenerateTimetableRequest, list[str]]:
    """Edit 을 조건에 반영한다. (새 조건, 바꾼 내용 설명)"""
    data = request.model_dump()
    done: list[str] = []
    name_of = {c.course_code: c.name for c in catalog} | {c.name: c.name for c in catalog}
    code_of = {c.name: c.course_code for c in catalog} | {c.course_code: c.course_code for c in catalog}
    for item in edit.remove:
        code = code_of.get(item)
        if not code:
            continue
        data["must_include"] = [x for x in data["must_include"] if x.split("-")[0] != code and x != name_of[code]]
        data["exclude"] = [*{*data["exclude"], code}]
        done.append(f"{name_of[code]} 뺐어")
    for item in edit.add:
        code = code_of.get(item)
        if not code:
            continue
        data["exclude"] = [x for x in data["exclude"] if x != code and x != name_of[code]]
        data["must_include"] = [*{*data["must_include"], code}]
        done.append(f"{name_of[code]} 넣었어")
    for day in edit.free_days:
        if day not in "월화수목금토일" or len(day) != 1 or day in data["free_days"]:
            continue
        data["free_days"].append(day)
        done.append(f"{day}요일 비웠어")
    for day in edit.unfree_days:
        if day in data["free_days"]:
            data["free_days"].remove(day)
            done.append(f"{day}요일 공강 풀었어")
    if edit.no_class_before is not None and 1 <= edit.no_class_before <= 23:
        start = f"{edit.no_class_before:02d}:00"
        data["blocked_times"] = [b for b in data["blocked_times"] if b["start"] != "00:00"] + [{"day": d, "start": "00:00", "end": start} for d in WEEKDAYS]
        done.append(f"평일 {edit.no_class_before}시 전 수업 뺐어")
    if edit.no_class_after is not None and 1 <= edit.no_class_after <= 23:
        end = f"{edit.no_class_after:02d}:00"
        data["blocked_times"] = [b for b in data["blocked_times"] if b["end"] != "24:00"] + [{"day": d, "start": end, "end": "24:00"} for d in WEEKDAYS]
        done.append(f"평일 {edit.no_class_after}시 뒤 수업 뺐어")
    if edit.target_credits is not None or edit.credits_delta:
        now = candidate.total_credits if candidate else request.target_credits
        target = edit.target_credits if edit.target_credits is not None else now + (edit.credits_delta or 0)
        target = max(0.0, min(float(planner.CREDIT_CAP), target))
        data["target_credits"] = target
        data["min_credits"] = min(data["min_credits"], target)
        data["max_credits"] = max(min(data["max_credits"], planner.CREDIT_CAP), target)
        done.append(f"목표 {target:g}학점으로 바꿨어")
    data["blocked_times"] = [DayTime(**b) for b in data["blocked_times"]]
    return GenerateTimetableRequest(**data), done


# ---------- 한 번 처리 ----------

HELP = "무엇을 바꿀지 잘 모르겠어. 예: '자료구조 빼줘', '운영체제 넣어줘', '금요일 비워줘', '아침 수업 싫어', '15학점으로 줄여줘'."


def handle(
    chat: PlanChatRequest,
    catalog: list[Course],
    ask: Callable[[str, Candidate | None, list[Course], list[ChatMessage]], Edit | None] = ask_model,
) -> PlanChatResponse:
    candidate = planner.store.get(chat.candidate_id)
    if not chat.message or not chat.message.strip():
        if candidate is None:
            return PlanChatResponse(reply="아직 설명할 시간표가 없어. 먼저 시간표를 만들어 줘.", applied=False, request=chat.request)
        return PlanChatResponse(reply=explain(candidate, chat.request), applied=False, request=chat.request)

    edit = ask(chat.message, candidate, catalog, chat.history) or parse_rules(chat.message, candidate, catalog)
    updated, done = apply(edit, chat.request, candidate, catalog)
    if not done:
        return PlanChatResponse(reply=edit.reply or HELP, applied=False, request=chat.request)

    response = planner.generate(updated.model_copy(update={"base_candidate_id": chat.candidate_id}), catalog)
    if not response.candidates:
        reason = " ".join(response.warnings) or "조건이 너무 빡빡해."
        return PlanChatResponse(reply=f"{', '.join(done)}. 그런데 그러면 맞는 시간표가 없어서 그대로 뒀어. {reason}", applied=False, request=chat.request)
    new = response.candidates[0]
    before = {s.name for s in candidate.sections} if candidate else set()
    after = {s.name for s in new.sections}
    diff = [f"빠진 과목: {', '.join(sorted(before - after))}"] if before - after else []
    diff += [f"새로 들어온 과목: {', '.join(sorted(after - before))}"] if candidate and after - before else []
    reply = "\n".join([edit.reply or ", ".join(done) + ".", *diff]) + "\n\n" + explain(new, updated, response)
    return PlanChatResponse(reply=reply, applied=True, request=updated, response=response)
