import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app
from app.schemas import Course, GraduationRequirement, Meeting
from app.services.course_repository import load_courses, using_sample_data

DATA = Path(__file__).parent.parent / "app" / "data"


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    """테스트마다 비어 있는 새 DB 를 쓴다."""
    monkeypatch.setenv("PLANNER_DB", str(tmp_path / "planner.db"))
    return tmp_path / "planner.db"


def real_course(course_id="REAL0001-001", semester="2학기", name="실제 과목") -> Course:
    return Course(
        year=2026, semester=semester, category="전공선택", department="컴퓨터학부",
        course_id=course_id, course_code=course_id.split("-")[0], section="001",
        name=name, credits=3,
        meetings=[Meeting(day="월", start="09:00", end="10:30"), Meeting(day="수", start="09:00", end="10:30")],
    )


def test_first_connection_creates_tables_and_seeds_sample(fresh_db):
    with db.connect() as connection:
        status = db.counts(connection)
    assert fresh_db.exists()
    assert status["courses"] == 8
    assert status["meetings"] == 13
    assert status["courses_sample"] is True
    assert status["programs"] == 1
    assert status["requirements_sample"] is True


def test_courses_read_from_db_match_the_source_file(fresh_db):
    from_file = load_courses(DATA / "courses.sample.json")
    from_db = load_courses()
    assert sorted(from_db, key=lambda c: c.course_id) == sorted(from_file, key=lambda c: c.course_id)
    assert using_sample_data()


def test_search_filters(fresh_db):
    with db.connect() as connection:
        assert {c.name for c in db.fetch_courses(connection, q="자료")} == {"자료구조(샘플)"}
        assert len(db.fetch_courses(connection, q="SAMP02")) == 3
        assert {c.category for c in db.fetch_courses(connection, category="교양")} == {"교양"}
        assert len(db.fetch_courses(connection, department="교양교육센터")) == 3
        assert db.fetch_courses(connection, q="자료", category="교양") == []


def test_real_courses_replace_the_sample(fresh_db):
    with db.connect() as connection:
        db.replace_courses(connection, [real_course()])
        status = db.counts(connection)
    assert status["courses"] == 1
    assert status["meetings"] == 2  # 샘플의 수업 시간도 함께 지워진다
    assert status["courses_sample"] is False
    assert [c.name for c in load_courses()] == ["실제 과목"]
    assert not using_sample_data()


def test_importing_again_replaces_only_that_semester(fresh_db):
    with db.connect() as connection:
        db.replace_courses(connection, [real_course("A0001-001", "1학기"), real_course("B0001-001", "2학기")])
        db.replace_courses(connection, [real_course("B0002-001", "2학기", name="바뀐 과목")])
        ids = {c.course_id for c in db.fetch_courses(connection)}
    assert ids == {"A0001-001", "B0002-001"}


def test_cache_follows_db_changes(fresh_db):
    assert len(load_courses()) == 8
    with db.connect() as connection:
        db.replace_courses(connection, [real_course()])
    assert len(load_courses()) == 1


def test_failed_write_is_rolled_back(fresh_db):
    with pytest.raises(RuntimeError):
        with db.connect() as connection:
            db.replace_courses(connection, [real_course()])
            raise RuntimeError("중간에 실패")
    assert len(load_courses()) == 8  # 샘플이 그대로 남아 있다


def test_requirements_round_trip(fresh_db):
    item = GraduationRequirement(
        department="컴퓨터학부", admission_year=2023, total_credits=140,
        credits={"전공필수": 33, "교양": 30},
        required_courses=[{"course_code": "REAL0001", "name": "실제 과목"}],
    )
    with db.connect() as connection:
        db.replace_requirements(connection, [item])
        assert db.fetch_requirements(connection) == [item]  # 샘플은 지워진다
        assert db.fetch_requirements(connection, department="컴퓨터학부", admission_year=2023) == [item]
        assert db.fetch_requirements(connection, admission_year=1999) == []
        assert db.counts(connection)["requirements_sample"] is False


def test_endpoints_use_the_db(fresh_db):
    client = TestClient(app)

    body = client.get("/courses").json()
    assert body["sample"] is True and len(body["courses"]) == 8
    assert [c["name"] for c in client.get("/courses", params={"q": "운영"}).json()["courses"]] == ["운영체제(샘플)"]

    requirements = client.get("/requirements").json()
    assert requirements["sample"] is True
    assert requirements["requirements"][0]["credits"]["전공필수"] == 30
    assert client.get("/requirements", params={"department": "없는학과"}).json()["requirements"] == []

    timetables = client.post("/timetables", json={"min_credits": 12, "max_credits": 15}).json()
    assert timetables["timetables"]


def test_import_script_loads_a_spreadsheet(fresh_db, tmp_path, monkeypatch, capsys):
    from scripts import import_data

    monkeypatch.setattr(db, "DATA_DIR", tmp_path)  # 실제 data 폴더에 courses.json 을 쓰지 않게
    monkeypatch.setattr("sys.argv", ["import_data", "courses", str(DATA / "courses.sample.csv")])
    import_data.main()

    assert "강좌 8개" in capsys.readouterr().out
    assert not using_sample_data()  # 파일에서 넣은 것은 실제 데이터로 취급한다
    saved = json.loads((tmp_path / "courses.json").read_text(encoding="utf-8"))
    assert len(saved) == 8 and saved[0]["meetings"]
