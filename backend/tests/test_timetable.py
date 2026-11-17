from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas import TimeBlock, TimetableRequest
from app.services.course_repository import load_courses
from app.services.timetable import generate_timetables, validate_timetable

SAMPLE = Path(__file__).parent.parent / "app" / "data" / "courses.sample.json"


@pytest.fixture
def courses():
    return load_courses(SAMPLE)


def codes(timetable) -> set[str]:
    return {course.course_code for course in timetable.courses}


def days(timetable) -> set[str]:
    return {meeting.day for course in timetable.courses for meeting in course.meetings}


def test_every_timetable_follows_the_rules(courses):
    result = generate_timetables(
        courses, TimetableRequest(min_credits=12, max_credits=18, max_results=20)
    )
    assert len(result.timetables) == 20
    assert not result.truncated
    for timetable in result.timetables:
        assert validate_timetable(timetable.courses) == []
        assert 12 <= timetable.total_credits <= 18
        assert timetable.total_credits == sum(c.credits for c in timetable.courses)


def test_results_are_sorted_by_score(courses):
    result = generate_timetables(courses, TimetableRequest(min_credits=9, max_credits=15))
    scores = [timetable.score for timetable in result.timetables]
    assert scores == sorted(scores, reverse=True)


def test_must_include_by_code_or_name(courses):
    request = TimetableRequest(
        min_credits=6, max_credits=12, must_include=["SAMP0301", "글쓰기(샘플)"]
    )
    result = generate_timetables(courses, request)
    assert result.timetables
    for timetable in result.timetables:
        assert {"SAMP0301", "SAMP0101"} <= codes(timetable)


def test_completed_and_excluded_courses_never_appear(courses):
    request = TimetableRequest(
        min_credits=6, max_credits=12, completed=["SAMP0201"], exclude=["세계의 문화(샘플)"]
    )
    for timetable in generate_timetables(courses, request).timetables:
        assert not codes(timetable) & {"SAMP0201", "SAMP0102"}


def test_blocked_times_are_respected(courses):
    request = TimetableRequest(
        min_credits=9,
        max_credits=15,
        blocked_times=[TimeBlock(day="금"), TimeBlock(start="09:00", end="10:00")],
    )
    result = generate_timetables(courses, request)
    assert result.timetables
    for timetable in result.timetables:
        assert "금" not in days(timetable)
        assert "금" in timetable.free_days
        for course in timetable.courses:
            assert all(meeting.start >= "10:00" for meeting in course.meetings)


def test_required_credits_by_category(courses):
    request = TimetableRequest(
        min_credits=9, max_credits=12, required_credits={"교양": 5, "전공필수": 3}
    )
    result = generate_timetables(courses, request)
    assert result.timetables
    for timetable in result.timetables:
        assert timetable.credits_by_category["교양"] >= 5
        assert timetable.credits_by_category["전공필수"] >= 3


def test_preferred_free_day_ranks_first(courses):
    request = TimetableRequest(min_credits=12, max_credits=15, preferred_free_days=["금"])
    best = generate_timetables(courses, request).timetables[0]
    assert "금" in best.free_days


def test_exclude_full_sections(courses):
    request = TimetableRequest(min_credits=3, max_credits=18, exclude_full=True, max_results=20)
    for timetable in generate_timetables(courses, request).timetables:
        for course in timetable.courses:
            assert course.enrolled < course.capacity


def test_impossible_requests_explain_why(courses):
    too_many = generate_timetables(courses, TimetableRequest(min_credits=30, max_credits=33))
    assert too_many.timetables == []
    assert "19학점" in too_many.message

    unknown = generate_timetables(
        courses, TimetableRequest(min_credits=3, max_credits=6, must_include=["없는과목"])
    )
    assert unknown.timetables == []
    assert "없는과목" in unknown.message

    blocked = generate_timetables(
        courses,
        TimetableRequest(
            min_credits=3,
            max_credits=6,
            must_include=["SAMP0101"],
            blocked_times=[TimeBlock(day="금")],
        ),
    )
    assert blocked.timetables == []
    assert "SAMP0101" in blocked.message


def test_validate_timetable_reports_problems(courses):
    by_id = {course.course_id: course for course in courses}
    overlapping = [by_id["SAMP0201-001"], by_id["SAMP0202-001"]]
    assert any("겹칩니다" in problem for problem in validate_timetable(overlapping))

    same_course = [by_id["SAMP0201-001"], by_id["SAMP0201-002"]]
    assert any("두 번" in problem for problem in validate_timetable(same_course))


def test_min_credits_cannot_exceed_max():
    with pytest.raises(ValidationError):
        TimetableRequest(min_credits=18, max_credits=12)


def test_endpoint_returns_timetables():
    client = TestClient(app)
    response = client.post(
        "/timetables",
        json={"min_credits": 12, "max_credits": 15, "preferred_free_days": ["금"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["timetables"]
    assert "금" in body["timetables"][0]["free_days"]

    assert client.post("/timetables", json={"min_credits": 18, "max_credits": 12}).status_code == 422


def test_courses_endpoint_lists_all_sections():
    body = TestClient(app).get("/courses").json()
    assert isinstance(body["sample"], bool)
    assert {"course_id", "course_code", "name", "credits", "meetings"} <= body["courses"][0].keys()


def test_home_page_is_served():
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "시간표 짜기" in response.text


def big_catalog(count=3000):
    """학교 전체 강좌만큼 큰 가짜 목록."""
    import random

    from app.schemas import Course, Meeting

    rng = random.Random(3)
    catalog = []
    for i in range(count):
        days = rng.sample("월화수목금", 2)
        hour = rng.randint(9, 16)
        for section in range(rng.randint(1, 2)):
            catalog.append(
                Course(
                    year=2026, semester="2학기",
                    category=rng.choice(["전공필수", "전공선택", "교양"]),
                    course_id=f"C{i:04d}-{section:03d}", course_code=f"C{i:04d}",
                    section=f"{section:03d}", name=f"과목{i}", credits=3,
                    meetings=[
                        Meeting(day=day, start=f"{hour:02d}:00", end=f"{hour + 1:02d}:30")
                        for day in days
                    ],
                )
            )
    return catalog


def test_large_catalog_is_fast_and_still_follows_the_rules():
    import time

    catalog = big_catalog()
    request = TimetableRequest(
        min_credits=15, max_credits=18, required_credits={"전공필수": 6},
        preferred_free_days=["금"], blocked_times=[TimeBlock(start="00:00", end="10:00")],
    )
    began = time.perf_counter()
    result = generate_timetables(catalog, request)
    elapsed = time.perf_counter() - began

    assert elapsed < 4, f"과목 3000개에서 {elapsed:.1f}초가 걸렸습니다"  # 고치기 전에는 약 7초
    assert result.truncated and len(result.timetables) == 5
    for timetable in result.timetables:
        assert validate_timetable(timetable.courses) == []
        assert 15 <= timetable.total_credits <= 18
        assert timetable.credits_by_category.get("전공필수", 0) >= 6
        assert all(m.start >= "10:00" for course in timetable.courses for m in course.meetings)
    assert "금" in result.timetables[0].free_days
    assert generate_timetables(catalog, request) == result  # 같은 요청에는 같은 결과


def test_large_catalog_keeps_the_current_timetable_after_an_edit():
    catalog = big_catalog()
    base = TimetableRequest(min_credits=15, max_credits=15)
    current = generate_timetables(catalog, base).timetables[0]
    ids = [course.course_id for course in current.courses]

    removed = current.courses[0]
    edited = base.model_copy(update={"exclude": [removed.course_code], "prefer_courses": ids})
    after = {course.course_id for course in generate_timetables(catalog, edited).timetables[0].courses}

    assert removed.course_id not in after
    assert set(ids) - {removed.course_id} <= after  # 뺀 과목 말고는 그대로
