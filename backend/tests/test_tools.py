"""에이전트 도구 정의 v3.2 의 generate_timetable, 실제 개설 강좌 가져오기."""

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app
from app.schemas import Course, CourseListing, GenerateTimetableRequest, Meeting
from app.services import planner
from app.services.course_repository import load_courses
from app.services.knu_offerings import courses_from_school_json
from app.services.timetable import validate_timetable

DATA = Path(__file__).parent.parent / "app" / "data"
client = TestClient(app)


def generate(**body):
    response = client.post("/tools/generate_timetable", json=body)
    assert response.status_code == 200, response.text
    return response.json()


def codes(candidate):
    return {section["course_code"] for section in candidate["sections"]}


def ids(candidate):
    return {section["course_id"] for section in candidate["sections"]}


def days(candidate):
    return {m["day"] for section in candidate["sections"] for m in section["meetings"]}


# ---------- 기본 동작 ----------


def test_success_returns_up_to_three_valid_candidates():
    body = generate(min_credits=6, target_credits=9, max_credits=12)
    assert body["status"] == "success" and body["optimal"] is False
    assert 1 <= len(body["candidates"]) <= 3
    assert len({c["id"] for c in body["candidates"]}) == len(body["candidates"])
    sample = {c.course_id: c for c in load_courses()}
    for candidate in body["candidates"]:
        assert candidate["id"].startswith("tt_")
        assert 6 <= candidate["total_credits"] <= 12
        assert validate_timetable([sample[i] for i in ids(candidate)]) == []
        assert "SAMP0103" not in codes(candidate)  # 시간 미정 강좌는 자동 추천에서 뺀다


def test_max_credits_are_capped_at_the_rule_limit():
    body = generate(min_credits=12, target_credits=18, max_credits=21)
    assert body["applied"]["max_credits"] == 19
    assert any("19학점" in warning for warning in body["warnings"])


def test_target_credits_are_preferred():
    low = generate(min_credits=3, target_credits=6, max_credits=12)["candidates"][0]
    high = generate(min_credits=3, target_credits=12, max_credits=12)["candidates"][0]
    assert abs(low["total_credits"] - 6) <= abs(high["total_credits"] - 6)
    assert high["total_credits"] >= low["total_credits"]


def test_free_days_and_blocked_times_are_hard():
    body = generate(min_credits=6, target_credits=9, max_credits=12,
                    free_days=["금"], blocked_times=[{"day": "월", "start": "09:00", "end": "12:00"}])
    assert body["status"] == "success"
    for candidate in body["candidates"]:
        assert "금" not in days(candidate)
        for section in candidate["sections"]:
            assert not any(m["day"] == "월" and m["start"] < "12:00" for m in section["meetings"])


def test_avoid_times_are_soft():
    body = generate(min_credits=6, target_credits=9, max_credits=12,
                    avoid_times=[{"day": "월", "start": "00:00", "end": "23:59"}])
    assert "월" in body["candidates"][0]["free_days"]


def test_must_include_by_section_and_exclude_by_section():
    body = generate(min_credits=6, target_credits=9, max_credits=12, must_include=["SAMP0201-002"])
    assert all("SAMP0201-002" in ids(c) and "SAMP0201-001" not in ids(c) for c in body["candidates"])
    body = generate(min_credits=6, target_credits=9, max_credits=12, exclude=["SAMP0201-001"])
    assert all("SAMP0201-001" not in ids(c) for c in body["candidates"])
    body = generate(min_credits=6, target_credits=9, max_credits=12, exclude=["자료구조(샘플)"])
    assert all("SAMP0201" not in codes(c) for c in body["candidates"])


# ---------- 일부만 지킬 수 있을 때 ----------


def test_must_course_on_a_free_day_gives_partial_with_an_alternative():
    body = generate(min_credits=6, target_credits=9, max_credits=12, must_include=["SAMP0101"], free_days=["금"])
    assert body["status"] == "partial"
    assert body["candidates"], "빠진 과목 말고 나머지로 시간표를 만든다"
    [omitted] = body["omitted_required"]
    assert omitted["reason"] == "free_day_conflict" and omitted["code"] == "SAMP0101"

    [alternative] = [a for a in body["alternatives"] if "금요일 공강" in a["relaxed"][0]]
    assert alternative["id"].startswith("tt_alt_")
    assert "글쓰기(샘플) 포함" in alternative["description"]
    assert "SAMP0101" in codes(alternative["candidate"])

    # 대안을 고르면 새로 풀지 않고 이미 만든 후보를 가져온다.
    fetched = client.get(f"/tools/candidates/{alternative['id']}").json()
    assert fetched["id"] == alternative["id"] and ids(fetched) == ids(alternative["candidate"])


@pytest.mark.parametrize(
    "body, reason",
    [
        ({"must_include": ["없는과목"]}, "not_offered"),
        ({"must_include": ["SAMP0201"], "completed": ["SAMP0201"]}, "already_completed"),
        ({"must_include": ["SAMP0201"], "exclude": ["SAMP0201"]}, "excluded"),
        ({"must_include": ["SAMP0201"], "blocked_times": [
            {"day": d, "start": "09:00", "end": "15:00"} for d in "월화수목"]}, "blocked_time"),
    ],
)
def test_omitted_required_reasons(body, reason):
    result = generate(min_credits=3, target_credits=6, max_credits=12, **body)
    assert result["status"] == "partial"
    assert [item["reason"] for item in result["omitted_required"]] == [reason]


def test_must_courses_that_clash_with_each_other():
    # 자료구조 001(월수 9:00) 만 허용하고 이산수학(월수 10:00)도 반드시 넣으라고 하면 함께 넣을 수 없다.
    result = generate(min_credits=3, target_credits=6, max_credits=12, must_include=["SAMP0201-001", "SAMP0202"])
    assert result["status"] == "partial"
    assert [item["reason"] for item in result["omitted_required"]] == ["time_conflict"]
    assert all("SAMP0201-001" in ids(c) for c in result["candidates"])


def test_minimum_credits_strict_vs_not():
    loose = generate(min_credits=19, target_credits=19, max_credits=19)
    assert loose["status"] == "partial" and any("최소" in w for w in loose["warnings"])
    strict = generate(min_credits=19, target_credits=19, max_credits=19, credits_strict=True)
    assert strict["status"] == "infeasible" and strict["candidates"] == []


# ---------- 이전 후보를 바탕으로 고치기 ----------


def test_base_candidate_keeps_the_other_courses():
    first = generate(min_credits=9, target_credits=12, max_credits=12)["candidates"][0]
    dropped = sorted(ids(first))[0]
    edited = generate(min_credits=6, target_credits=9, max_credits=12,
                      base_candidate_id=first["id"], exclude=[dropped])
    assert edited["applied"]["base_candidate_id"] == first["id"]
    best = edited["candidates"][0]
    assert dropped not in ids(best)
    assert ids(first) - {dropped} <= ids(best)

    unknown = generate(min_credits=6, target_credits=9, max_credits=12, base_candidate_id="tt_999999")
    assert any("tt_999999" in warning for warning in unknown["warnings"])
    assert client.get("/tools/candidates/tt_999999").status_code == 404


def test_bad_requests_are_rejected():
    assert client.post("/tools/generate_timetable", json={"min_credits": 18, "target_credits": 15}).status_code == 422
    assert client.post("/tools/generate_timetable", json={"free_days": ["Fri"]}).status_code == 422
    bad_time = {"blocked_times": [{"day": "월", "start": "12:00", "end": "09:00"}]}
    assert client.post("/tools/generate_timetable", json=bad_time).status_code == 422


# ---------- 트랙별 이수구분 ----------


def course_with_listings():
    return Course(
        year=2026, semester="2학기", category="공학전공", course_id="CAIB0211-001", course_code="CAIB0211",
        name="자연어처리개론", credits=3, meetings=[Meeting(day="화", start="09:00", end="10:30")],
        listings=[
            CourseListing(source="computing", category="공학전공", grade="4"),
            CourseListing(source="ai", category="전공", grade="3"),
            CourseListing(source="core-humanities", category="교양", grade="*"),
        ],
    )


def test_category_follows_the_students_track():
    course = course_with_listings()
    assert (planner.for_track(course, "ai").category, planner.for_track(course, "ai").grade) == ("전공", "3")
    assert planner.for_track(course, "platform").category == "공학전공"  # 그 트랙 자료가 없으면 컴학 공통
    assert planner.for_track(course, None).area == "첨성인핵심 · 인문"


def test_school_json_is_merged_per_section(tmp_path):
    row = {
        "crseNo": "COMP0204-001", "sbjetCd": "COMP0204", "sbjetNm": "자료구조", "sbjetDvnno": "001",
        "estblYear": "2026", "estblSmstrSctnm": "2학기", "estblGrade": "2", "sbjetSctnm": "전공필수",
        "estblDprtnNm": "컴퓨터학부", "crdit": "3", "totalPrfssNm": "홍길동",
        "lssnsTimeInfo": "월 1A,1B,2A,수 1A,1B,2A", "lssnsRealTimeInfo": "월 09:00 ~ 10:30,수 09:00 ~ 10:30",
        "lctrmInfo": "산격동 캠퍼스  IT대학5호관", "rmnmCd": "101", "attlcPrscpCnt": 60, "appcrCnt": 72,
    }
    (tmp_path / "computing.json").write_text(json.dumps({"data": [row]}, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "ai.json").write_text(
        json.dumps({"data": [{**row, "sbjetSctnm": "전공기반", "estblGrade": "1"}]}, ensure_ascii=False), encoding="utf-8"
    )
    [course], warnings = courses_from_school_json(sorted(tmp_path.glob("*.json")))
    assert warnings == []
    assert [(x.source, x.category, x.grade) for x in course.listings] == [("computing", "전공필수", "2"), ("ai", "전공기반", "1")]
    assert course.category == "전공필수"  # 컴학 공통이 기본
    assert [(m.day, m.start, m.end) for m in course.meetings] == [("월", "09:00", "10:30"), ("수", "09:00", "10:30")]
    assert (course.capacity, course.enrolled) == (60, 72)


def test_sample_db_is_replaced_once_real_data_appears(tmp_path, monkeypatch):
    monkeypatch.setenv("PLANNER_DB", str(tmp_path / "planner.db"))
    monkeypatch.setattr(db, "DATA_DIR", tmp_path)
    (tmp_path / "courses.sample.json").write_text((DATA / "courses.sample.json").read_text(encoding="utf-8"), encoding="utf-8")
    with db.connect() as connection:
        assert db.counts(connection)["courses_sample"] is True

    real = course_with_listings().model_dump()
    (tmp_path / "courses.json").write_text(json.dumps([real], ensure_ascii=False), encoding="utf-8")
    monkeypatch.delenv("PLANNER_SEED", raising=False)
    db._ready.clear()  # 서버를 다시 켠 것처럼
    with db.connect() as connection:
        [course] = db.fetch_courses(connection)
        assert db.counts(connection)["courses_sample"] is False
    assert [x.source for x in course.listings] == ["computing", "ai", "core-humanities"]


# ---------- 실제 개설 강좌 ----------


@pytest.mark.skipif(not (DATA / "courses.json").exists(), reason="실제 개설 강좌 자료가 없음")
def test_real_catalog_follows_the_rules_and_is_fast():
    catalog = load_courses(DATA / "courses.json")
    assert len(catalog) > 500
    request = GenerateTimetableRequest(
        min_credits=15, target_credits=18, max_credits=21, track="advanced", grade=2,
        free_days=["금"], blocked_times=[{"day": "월", "start": "09:00", "end": "12:00"}],
    )
    began = time.perf_counter()
    result = planner.generate(request, catalog)
    elapsed = time.perf_counter() - began
    assert elapsed < 6, f"{elapsed:.1f}초"
    assert result.status == "success" and result.candidates
    for candidate in result.candidates:
        assert validate_timetable(candidate.sections) == []
        assert 15 <= candidate.total_credits <= 19
        assert "금" in candidate.free_days
        assert not any("상주" in (s.building or "") for s in candidate.sections)
        assert not any(m.day == "월" and m.start < "12:00" for s in candidate.sections for m in s.meetings)


# ---------- 점수: 주말 수업, 선수과목 (신청 인원·정원은 보지 않는다) ----------


def _course(**update):
    base = Course(
        year=2026, semester="2학기", category="전공", course_id="TEST0001-001", course_code="TEST0001",
        name="테스트", credits=3, meetings=[Meeting(day="월", start="09:00", end="10:30")],
    )
    return base.model_copy(update=update)


def test_weekend_sections_are_scored_lower_and_capacity_is_ignored():
    plain = planner.fit_bonus(_course(), None, None)
    assert planner.fit_bonus(_course(capacity=60, enrolled=90), None, None) == plain
    assert planner.fit_bonus(_course(meetings=[Meeting(day="토", start="09:00", end="12:00")]), None, None) < plain - 2
    assert planner.fit_bonus(_course(capacity=60, enrolled=59), None, None) == plain


def test_missing_prerequisite_lowers_score_and_warns_only_when_completed_is_given():
    algo = _course(name="알고리즘2", course_code="TEST0002", course_id="TEST0002-001")
    plan = planner._Plan(GenerateTimetableRequest(completed_names=["프로그래밍기초"]), [algo])
    assert plan.fit.get(algo.course_id, 0) <= -planner.PREREQ_PENALTY
    assert plan.prereq_missing(algo)
    done = planner._Plan(GenerateTimetableRequest(completed_names=["알고리즘1"]), [algo])
    assert not done.prereq_missing(algo)
    unknown = planner._Plan(GenerateTimetableRequest(), [algo])
    assert not unknown.prereq_missing(algo)  # 이수 기록이 없으면 판단하지 않는다


def test_no_empty_candidate_when_every_day_is_blocked():
    body = generate(min_credits=3, target_credits=3, max_credits=3, free_days=list("월화수목금토일"))
    assert body["status"] == "infeasible" and body["candidates"] == []
    assert body["warnings"]
