"""나의 시간표 챗봇. AI 없이(규칙) 설명하고, 말대로 시간표를 다시 만드는지 본다."""

from fastapi.testclient import TestClient

from app.agent import plan_chat
from app.main import app
from app.schemas import GenerateTimetableRequest
from app.services import planner
from app.services.course_repository import load_courses

client = TestClient(app)
no_ai = lambda *_: None


def first_candidate():
    request = GenerateTimetableRequest(track="advanced", grade=2)
    response = planner.generate(request, load_courses())
    assert response.candidates
    return request, response.candidates[0]


def test_explains_why_without_message():
    request, candidate = first_candidate()
    answer = plan_chat.handle(plan_chat.PlanChatRequest(request=request, candidate_id=candidate.id), load_courses(), ask=no_ai)
    assert not answer.applied
    assert f"{candidate.total_credits:g}학점" in answer.reply
    assert all(section.name in answer.reply for section in candidate.sections)


def test_free_day_and_remove_course_rebuild_timetable():
    request, candidate = first_candidate()
    busy = next(m.day for s in candidate.sections for m in s.meetings)
    answer = plan_chat.handle(plan_chat.PlanChatRequest(message=f"{busy}요일 비워줘", request=request, candidate_id=candidate.id), load_courses(), ask=no_ai)
    assert answer.applied and busy in answer.request.free_days
    assert all(m.day != busy for s in answer.response.candidates[0].sections for m in s.meetings)

    gone = candidate.sections[0]
    answer = plan_chat.handle(plan_chat.PlanChatRequest(message=f"{gone.name} 빼줘", request=request, candidate_id=candidate.id), load_courses(), ask=no_ai)
    assert answer.applied and gone.course_code in answer.request.exclude
    assert all(s.course_code != gone.course_code for s in answer.response.candidates[0].sections)


def test_rules_parse_common_phrases():
    edit = plan_chat.parse_rules("아침 수업 싫어, 15학점으로 해줘", None, [])
    assert (edit.no_class_before, edit.target_credits) == (10, 15)
    assert plan_chat.parse_rules("금요일 빼줘", None, []).free_days == ["금"]
    assert plan_chat.parse_rules("금요일 수업 있어도 돼", None, []).unfree_days == ["금"]


def test_unknown_message_keeps_request():
    request, candidate = first_candidate()
    answer = plan_chat.handle(plan_chat.PlanChatRequest(message="안녕", request=request, candidate_id=candidate.id), load_courses(), ask=no_ai)
    assert not answer.applied and answer.request == request


def test_endpoint():
    request, candidate = first_candidate()
    body = {"request": request.model_dump(), "candidate_id": candidate.id}
    assert client.post("/tools/chat", json=body).status_code == 200


# ---------- 규칙 모드 steps, 새 말들 ----------


def ask_rules(message, request, candidate, **extra):
    chat = plan_chat.PlanChatRequest(message=message, request=request, candidate_id=candidate.id, **extra)
    return plan_chat.handle(chat, load_courses(), ask=no_ai)


def test_rules_mode_fills_steps_and_previous_id():
    request, candidate = first_candidate()
    answer = ask_rules("금요일 비워줘", request, candidate)
    assert answer.mode == "rules" and answer.applied
    assert answer.previous_candidate_id == candidate.id
    labels = [s.label for s in answer.steps]
    assert labels[0] == "말 이해(규칙)" and answer.steps[0].detail == "금요일 공강"
    assert any(label.startswith("조건 반영: 금요일 비웠어") for label in labels)
    assert any(label.startswith("시간표 다시 생성:") for label in labels)
    assert any(label.startswith("검증: 시간 겹침 0") for label in labels)
    assert all(s.ok for s in answer.steps)


def test_explain_steps_and_endpoint_fields():
    request, candidate = first_candidate()
    body = client.post("/tools/chat", json={"request": request.model_dump(), "candidate_id": candidate.id}).json()
    assert body["mode"] in ("rules", "ai") and [s["label"] for s in body["steps"]][:2] == ["후보 분석", "근거 정리"]
    assert body["previous_candidate_id"] == candidate.id and body["select_candidate"] is None


def test_category_add_and_remove():
    request, candidate = first_candidate()
    majors = [s for s in candidate.sections if "전공" in s.category]
    answer = ask_rules("전공 하나 빼줘", request, candidate)
    assert answer.applied
    new_majors = [s for s in answer.response.candidates[0].sections if "전공" in s.category]
    assert len(new_majors) == len(majors) - 1

    request = GenerateTimetableRequest(track="advanced", grade=2, target_credits=3, min_credits=3, max_credits=3)
    small = planner.generate(request, load_courses()).candidates[0]
    assert all(s.category != "교양" for s in small.sections)
    ge = sum(1 for s in small.sections if s.category == "교양")
    answer = ask_rules("교양 하나 더 넣어줘", request, small)
    assert answer.applied, answer.reply
    assert sum(1 for s in answer.response.candidates[0].sections if s.category == "교양") == ge + 1


def test_first_period_and_course_not_in_timetable():
    request, candidate = first_candidate()
    assert plan_chat.parse_rules("1교시 피하고 싶어", None, []).no_class_before == 10
    missing = next(c for c in load_courses() if c.course_code not in {s.course_code for s in candidate.sections})
    present = candidate.sections[0]
    answer = ask_rules(f"{missing.name.split('(')[0]} 빼줘", request, candidate)
    assert not answer.applied and "지금 시간표에 없어" in answer.reply
    answer = ask_rules(f"{present.name.split('(')[0]} 넣어줘", request, candidate)
    assert not answer.applied and "이미 들어 있어" in answer.reply


def test_why_and_select_candidate():
    request, candidate = first_candidate()
    section = candidate.sections[0]
    answer = ask_rules(f"왜 {section.name.split('(')[0]} 넣었어?", request, candidate)
    assert not answer.applied and section.name in answer.reply
    answer = ask_rules("2안으로 바꿔줘", request, candidate, candidate_ids=[candidate.id, "tt_x2"])
    assert answer.select_candidate == "tt_x2" and not answer.applied
    answer = ask_rules("안녕", request, candidate)
    assert "빼줘" in answer.reply and not answer.applied


def test_prerequisite_chain_in_template(monkeypatch):
    request, candidate = first_candidate()
    target = candidate.sections[0]
    rows = [{"chain": "공통 · 프로그래밍", "required": "선행과목", "satisfied": True, "page": 1}]
    fake = type("M", (), {"check": staticmethod(lambda course, completed, catalog, track=None: rows if course == target.course_code else [])})
    monkeypatch.setitem(__import__("sys").modules, "app.services.prerequisites", fake)
    from app import services

    monkeypatch.setattr(services, "prerequisites", fake, raising=False)
    text = plan_chat.explain(candidate, request, None, load_courses())
    assert "선행과목을 들었으니 이어서 듣는 과목 (공통 · 프로그래밍)" in text


# ---------- AI 에이전트 루프 (가짜 OpenAI) ----------

from types import SimpleNamespace as NS


class FakeOpenAI:
    """정해 둔 답을 차례로 돌려주고, 받은 요청을 기록한다."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []
        self.chat = NS(completions=NS(create=self.create))

    def create(self, **kwargs):
        self.calls.append(kwargs)
        message = self.script.pop(0)
        return NS(choices=[NS(message=message)])


def tool_call(id_, name, **args):
    import json

    return NS(id=id_, type="function", function=NS(name=name, arguments=json.dumps(args, ensure_ascii=False)))


def test_agent_loop_calls_tools_and_fills_steps():
    request, candidate = first_candidate()
    busy = next(m.day for s in candidate.sections for m in s.meetings)
    fake = FakeOpenAI([
        NS(content=None, tool_calls=[tool_call("c1", "get_current_timetable"), tool_call("c2", "search_courses", query="운영체제")]),
        NS(content=None, tool_calls=[tool_call("c3", "check_prerequisites", course="운영체제")]),
        NS(content=None, tool_calls=[tool_call("c4", "apply_changes", free_days=[busy])]),
        NS(content=f"{busy}요일 비웠어.", tool_calls=None),
    ])
    chat = plan_chat.PlanChatRequest(message=f"{busy}요일 비워줘", request=request, candidate_id=candidate.id)
    answer = plan_chat.handle(chat, load_courses(), ask=lambda: (fake, "fake-model"))
    assert answer.mode == "ai" and answer.applied and answer.reply == f"{busy}요일 비웠어."
    assert busy in answer.request.free_days
    assert all(m.day != busy for s in answer.response.candidates[0].sections for m in s.meetings)
    tools = [s.tool for s in answer.steps]
    assert tools[:3] == ["get_current_timetable", "search_courses", "check_prerequisites"]
    assert "apply_changes" in tools and "verify" in tools and tools[-1] == "reply"
    assert next(s for s in answer.steps if s.tool == "search_courses").detail.endswith("개 찾음")
    assert answer.previous_candidate_id == candidate.id
    # 도구 결과가 AI 에게 다시 전달됐다
    last_messages = fake.calls[-1]["messages"]
    assert sum(1 for m in last_messages if m["role"] == "tool") == 4
    assert fake.calls[0]["tools"] and fake.calls[0]["tool_choice"] == "auto"


def test_agent_stops_after_max_steps():
    request, candidate = first_candidate()
    loop = [NS(content=None, tool_calls=[tool_call(f"c{i}", "get_current_timetable")]) for i in range(5)]
    fake = FakeOpenAI([*loop, NS(content="그대로 뒀어.", tool_calls=None)])
    chat = plan_chat.PlanChatRequest(message="음", request=request, candidate_id=candidate.id)
    answer = plan_chat.handle(chat, load_courses(), ask=lambda: (fake, "m"))
    assert len(fake.calls) == 6 and fake.calls[-1]["tool_choice"] == "none"
    assert answer.mode == "ai" and not answer.applied and answer.reply == "그대로 뒀어."


def test_agent_failure_falls_back_to_rules():
    request, candidate = first_candidate()

    class Broken:
        chat = NS(completions=NS(create=lambda **_: (_ for _ in ()).throw(RuntimeError("down"))))

    chat = plan_chat.PlanChatRequest(message="금요일 비워줘", request=request, candidate_id=candidate.id)
    answer = plan_chat.handle(chat, load_courses(), ask=lambda: (Broken(), "m"))
    assert answer.mode == "rules" and answer.applied
    assert answer.steps[0].tool == "ai" and not answer.steps[0].ok


def test_ai_explanation_uses_facts_only():
    request, candidate = first_candidate()
    fake = FakeOpenAI([NS(content="설명이야.", tool_calls=None)])
    chat = plan_chat.PlanChatRequest(request=request, candidate_id=candidate.id)
    answer = plan_chat.handle(chat, load_courses(), ask=lambda: (fake, "m"))
    assert answer.mode == "ai" and answer.reply == "설명이야."
    facts = fake.calls[0]["messages"][1]["content"]
    assert all(s.name in facts for s in candidate.sections)


def test_no_key_means_rules(monkeypatch):
    monkeypatch.setattr(plan_chat, "load_dotenv", lambda: None)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert plan_chat.connect() is None


def test_real_prerequisite_chain_reason():
    """실제 선수과목 자료: 자료구조를 들었으면 다음 단계 과목 설명에 사슬 근거가 붙는다."""
    from app.schemas import Course, Meeting

    algo = Course(year=2026, semester="2학기", category="전공선택", course_id="ALGO-001", course_code="ALGO", name="알고리즘1", credits=3,
                  meetings=[Meeting(day="월", start="09:00", end="10:30")])
    request = GenerateTimetableRequest(completed=["자료구조"])
    reason = plan_chat.prerequisite_reason(algo, request.completed, [algo])
    assert reason and reason.startswith("자료구조를 들었으니")
    assert plan_chat.prerequisite_reason(algo, [], [algo]) is None  # 이수 과목을 모르면 단정하지 않는다
