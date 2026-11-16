"""채팅 처리 테스트. 실제 OpenAI 를 부르지 않고, AI 의 답을 흉내 낸 함수를 넣어 확인한다."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.agent import chat as chat_module
from app.agent.chat import (
    AiAnswer,
    AiConditions,
    AiTimeBlock,
    find_candidates,
    handle_chat,
    to_ai_conditions,
)
from app.main import app
from app.schemas import ChatRequest, Course, Meeting, TimetableRequest
from app.services.course_repository import load_courses
from app.services.timetable import generate_timetables, validate_timetable

SAMPLE = Path(__file__).parent.parent / "app" / "data" / "courses.sample.json"


@pytest.fixture
def courses():
    return load_courses(SAMPLE)


@pytest.fixture
def base():
    return TimetableRequest(min_credits=9, max_credits=12)


def fake_ai(change, reply="바꿨습니다."):
    """받은 조건에 change 를 적용해 돌려주는 가짜 AI."""
    seen = {}

    def ask(payload, history):
        seen["payload"] = json.loads(payload)
        seen["history"] = history
        conditions = AiConditions(**seen["payload"]["조건"])
        change(conditions)
        return AiAnswer(reply=reply, conditions=conditions)

    ask.seen = seen
    return ask


def current_ids(courses, request):
    return [c.course_id for c in generate_timetables(courses, request).timetables[0].courses]


def test_adding_a_course_keeps_the_rest_of_the_timetable(courses, base):
    before = current_ids(courses, base)
    assert "SAMP0102-001" not in before

    def add(conditions):
        conditions.must_include.append("SAMP0102")
        conditions.max_credits += 3

    ask = fake_ai(add, "세계의 문화(샘플)를 추가했습니다.")
    response = handle_chat(
        ChatRequest(message="세계의 문화 추가해줘", request=base, current_course_ids=before),
        courses,
        ask,
    )

    assert response.applied
    assert response.reply == "세계의 문화(샘플)를 추가했습니다."
    assert response.request.must_include == ["SAMP0102"]
    assert response.request.prefer_courses == []  # 화면에 돌려주는 조건에는 남기지 않는다
    after = [course.course_id for course in response.result.timetables[0].courses]
    assert "SAMP0102-001" in after
    assert set(before) <= set(after)  # 원래 듣던 과목은 그대로
    assert validate_timetable(response.result.timetables[0].courses) == []


def test_removing_a_course(courses, base):
    before = current_ids(courses, base)
    removed = before[0].split("-")[0]

    def remove(conditions):
        conditions.exclude.append(removed)
        conditions.min_credits = 6

    response = handle_chat(
        ChatRequest(message="이 과목 빼줘", request=base, current_course_ids=before),
        courses,
        fake_ai(remove),
    )
    assert response.applied
    for timetable in response.result.timetables:
        assert removed not in {course.course_code for course in timetable.courses}


def test_ai_sees_conditions_current_timetable_and_candidates(courses, base):
    before = current_ids(courses, base)
    ask = fake_ai(lambda conditions: None)
    handle_chat(
        ChatRequest(message="교양 하나 추가해줘", request=base, current_course_ids=before),
        courses,
        ask,
    )
    payload = ask.seen["payload"]
    assert payload["사용자의 말"] == "교양 하나 추가해줘"
    assert payload["조건"]["max_credits"] == 12
    assert {item["code"] for item in payload["지금 시간표"]} == {i.split("-")[0] for i in before}
    assert {"SAMP0101", "SAMP0102", "SAMP0103"} <= {item["code"] for item in payload["후보 과목"]}


def test_unchanged_conditions_are_not_applied(courses, base):
    response = handle_chat(
        ChatRequest(message="안녕", request=base),
        courses,
        fake_ai(lambda conditions: None, "어떤 과목을 바꿀까요?"),
    )
    assert not response.applied
    assert response.result is None
    assert response.reply == "어떤 과목을 바꿀까요?"


def test_impossible_change_is_rejected_and_conditions_kept(courses, base):
    def too_many(conditions):
        conditions.min_credits, conditions.max_credits = 40, 45

    response = handle_chat(
        ChatRequest(message="40학점 듣고 싶어", request=base), courses, fake_ai(too_many)
    )
    assert not response.applied
    assert response.request == base
    assert "적용하지 않았습니다" in response.reply


def test_invented_courses_and_bad_times_are_dropped(courses, base):
    def invent(conditions):
        conditions.must_include += ["없는과목", "글쓰기(샘플)"]
        conditions.blocked_times += [
            AiTimeBlock(day="매일", start="00:00", end="10:00"),
            AiTimeBlock(day="금", start="오전", end="점심"),
        ]

    response = handle_chat(
        ChatRequest(message="글쓰기랑 없는과목 넣어줘", request=base), courses, fake_ai(invent)
    )
    # 형식이 틀린 시간과 없는 과목은 버려지고, 남은 조건(글쓰기 꼭 넣기 + 10시 이전 금지)은
    # 글쓰기가 금 09:00 수업이라 서로 충돌하므로 적용되지 않아야 한다.
    assert not response.applied
    assert response.request == base


def test_invented_course_is_reported(courses, base):
    def invent(conditions):
        conditions.must_include += ["없는과목", "운영체제(샘플)"]

    response = handle_chat(
        ChatRequest(message="운영체제랑 없는과목 넣어줘", request=base), courses, fake_ai(invent)
    )
    assert response.applied
    assert response.request.must_include == ["SAMP0301"]
    assert "없는과목" in response.reply


def test_invalid_credit_range_from_ai_is_handled(courses, base):
    def broken(conditions):
        conditions.min_credits, conditions.max_credits = 18, 12

    response = handle_chat(ChatRequest(message="?", request=base), courses, fake_ai(broken))
    assert not response.applied
    assert response.request == base


def test_conditions_round_trip(courses):
    request = TimetableRequest(
        min_credits=9,
        max_credits=15,
        must_include=["SAMP0301"],
        blocked_times=[{"day": "금"}, {"start": "00:00", "end": "10:00"}],
        required_credits={"교양": 3},
        preferred_free_days=["월"],
    )
    restored, dropped = chat_module.from_ai_conditions(to_ai_conditions(request), request, courses)
    assert restored == request
    assert dropped == []


def test_find_candidates_narrows_a_large_catalog():
    names = ["자료구조", "세계의 문화", "미분적분학", "글쓰기"]
    catalog = [
        Course(
            year=2026, semester="2학기", category="교양" if i % 2 else "전공선택",
            course_id=f"X{i:04d}-001", course_code=f"X{i:04d}",
            name=names[i] if i < len(names) else f"과목{i}", credits=3,
            meetings=[Meeting(day="월", start="09:00", end="10:00")],
        )
        for i in range(200)
    ]
    found = find_candidates("세계의문화 추가해줘", catalog)
    assert len(found) <= 40
    assert found[0]["name"] == "세계의 문화"


def test_endpoint_explains_missing_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(chat_module, "load_dotenv", lambda: None)
    response = TestClient(app).post(
        "/chat", json={"message": "금요일 비워줘", "request": {"min_credits": 9, "max_credits": 12}}
    )
    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]
