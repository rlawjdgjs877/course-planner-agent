"""시간표 에이전트(/agent/chat) 테스트. 실제 Claude 를 부르지 않고, 정해 둔 응답을 차례로 돌려주는 가짜를 쓴다."""

import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.agent import claude as claude_module
from app.agent import planner_agent
from app.agent.planner_agent import AgentChatRequest, apply_changes, handle
from app.main import app
from app.schemas import GenerateTimetableRequest
from app.services import planner, prerequisites
from app.services.course_repository import load_courses
from app.services.timetable import validate_timetable


def text(value):
    return SimpleNamespace(type="text", text=value)


def tool(name, **args):
    tool.count = getattr(tool, "count", 0) + 1
    return SimpleNamespace(type="tool_use", id=f"toolu_{tool.count}", name=name, input=args)


def turn(*blocks):
    stop = "tool_use" if any(b.type == "tool_use" for b in blocks) else "end_turn"
    return SimpleNamespace(content=list(blocks), stop_reason=stop)


def scripted(*turns):
    """정해 둔 응답을 차례로 돌려주고, 받은 메시지를 기록한다."""
    seen: list[list[dict]] = []
    queue = list(turns)

    def ask(messages):
        seen.append(list(messages))
        return queue.pop(0)

    ask.seen = seen
    return ask


NO_CHANGE = dict(
    add_courses=[], remove_courses=[], release_courses=[], mark_completed=[], free_days_add=[],
    free_days_remove=[], preferred_free_days_add=[], blocked_times_add=[], avoid_times_add=[],
    clear_time_preferences=False, min_credits=None, target_credits=None, max_credits=None,
    ge_areas=None, prefer_professor=None,
)


@pytest.fixture
def courses():
    return load_courses()


@pytest.fixture
def base():
    return GenerateTimetableRequest(min_credits=6, target_credits=9, max_credits=12)


@pytest.fixture
def first(courses, base):
    return planner.generate(base, courses).candidates[0]


def test_summary_sends_current_timetable_without_changing_it(courses, base, first):
    ask = scripted(turn(text("9학점 시간표예요.")))
    response = handle(AgentChatRequest(mode="summary", request=base, candidate_id=first.id), courses, ask)
    assert response.reply == "9학점 시간표예요."
    assert response.applied is False and response.result is None
    prompt = ask.seen[0][-1]["content"]
    assert first.id in prompt and first.sections[0].name in prompt


def test_summary_without_a_timetable_does_not_call_claude(courses, base):
    def never(_):
        raise AssertionError("Claude 를 부르면 안 된다")

    response = handle(AgentChatRequest(mode="summary", request=base, candidate_id="tt_없음"), courses, never)
    assert "다시 만들어" in response.reply


def test_free_day_request_rebuilds_the_timetable(courses, base, first):
    day = next(m.day for s in first.sections for m in s.meetings)
    ask = scripted(
        turn(tool("update_timetable", **{**NO_CHANGE, "free_days_add": [day]})),
        turn(text(f"{day}요일을 비웠어요.")),
    )
    response = handle(AgentChatRequest(message=f"{day}요일 비워줘", request=base, candidate_id=first.id), courses, ask)
    assert response.applied
    assert response.request.free_days == [day]
    new = response.result.candidates[0]
    assert day not in {m.day for s in new.sections for m in s.meetings}
    assert validate_timetable(new.sections) == []
    assert [s.tool for s in response.steps] == ["update_timetable"]
    # 도구 결과가 Claude 에게 돌아갔다
    result = json.loads(ask.seen[1][-1]["content"][0]["content"])
    assert result["새 시간표"]["id"] == new.id


def test_impossible_change_keeps_the_timetable(courses, base, first):
    ask = scripted(
        turn(tool("update_timetable", **{**NO_CHANGE, "free_days_add": ["월", "화", "수", "목", "금", "토", "일"], "min_credits": 12})),
        turn(text("그렇게는 만들 수 없어요.")),
    )
    response = handle(AgentChatRequest(message="다 비워줘", request=base, candidate_id=first.id), courses, ask)
    assert response.applied is False and response.result is None
    assert response.request.free_days == []
    assert response.steps[0].ok is False


def test_search_then_add_a_course(courses, base, first):
    taken = {s.course_code for s in first.sections}
    target = next(c for c in courses if c.course_code not in taken and not planner.not_recommended(c))
    ask = scripted(
        turn(tool("search_courses", query=target.name, category=None, area=None, day=None, grade=None, fits_current=False)),
        turn(tool("update_timetable", **{**NO_CHANGE, "add_courses": [target.course_code]})),
        turn(text("넣었어요.")),
    )
    response = handle(AgentChatRequest(message=f"{target.name} 넣어줘", request=base, candidate_id=first.id), courses, ask)
    found = json.loads(ask.seen[1][-1]["content"][0]["content"])
    assert found["과목"][0]["과목코드"] == target.course_code
    assert response.applied
    assert target.course_code in {s.course_code for s in response.result.candidates[0].sections}
    assert target.course_code in response.request.must_include


def test_unknown_tool_is_reported_back_not_raised(courses, base, first):
    ask = scripted(turn(tool("delete_everything")), turn(text("그건 못 해요.")))
    response = handle(AgentChatRequest(message="?", request=base, candidate_id=first.id), courses, ask)
    assert response.reply == "그건 못 해요."
    assert ask.seen[1][-1]["content"][0]["is_error"] is True


def test_history_starts_with_a_user_message(courses, base, first):
    ask = scripted(turn(text("네.")))
    history = [{"role": "assistant", "content": "요약"}, {"role": "user", "content": "고마워"}, {"role": "assistant", "content": "천만에요"}]
    handle(AgentChatRequest(message="하나 더", request=base, candidate_id=first.id, history=history), courses, ask)
    assert ask.seen[0][0]["role"] == "user"


def test_apply_changes_keeps_credit_order(courses, base):
    updated = apply_changes(base, {**NO_CHANGE, "target_credits": 15}, courses)
    assert updated.min_credits <= updated.target_credits == 15 <= updated.max_credits
    updated = apply_changes(base, {**NO_CHANGE, "max_credits": 3}, courses)
    assert updated.min_credits <= updated.target_credits <= updated.max_credits == 3


def test_apply_changes_moves_courses_between_lists(courses):
    base = GenerateTimetableRequest(must_include=["A"], exclude=["B"])
    updated = apply_changes(base, {**NO_CHANGE, "add_courses": ["B"], "remove_courses": ["A"]}, courses)
    assert updated.must_include == ["B"] and updated.exclude == ["A"]


def test_endpoint_explains_missing_api_key(monkeypatch, base):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.setattr(claude_module, "load_dotenv", lambda: None)
    response = TestClient(app).post("/agent/chat", json={"message": "안녕", "request": base.model_dump()})
    assert response.status_code == 503
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]


def test_tools_are_strict_and_list_every_property():
    for definition in planner_agent.TOOLS:
        schema = definition["input_schema"]
        assert definition["strict"] is True and schema["additionalProperties"] is False
        assert set(schema["required"]) == set(schema["properties"])


# ---------- 선수과목 (학과 권장 순서) ----------


def test_prerequisite_stages_accept_any_alternative():
    assert ("자료구조", "자료구조응용") in prerequisites.missing("알고리즘1", set())
    done = {prerequisites.normalize("자료구조응용"), prerequisites.normalize("자료구조")}
    assert prerequisites.missing("알고리즘1", done) == []
    assert prerequisites.missing("없는과목", set()) == []


def test_backend_and_frontend_prerequisite_data_match():
    from pathlib import Path

    root = Path(__file__).parent.parent.parent
    backend = json.loads((root / "backend/app/data/prerequisites.json").read_text(encoding="utf-8"))
    frontend = json.loads((root / "frontend/app/lib/data/prerequisites.json").read_text(encoding="utf-8"))
    assert backend == frontend
