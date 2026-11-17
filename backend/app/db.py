"""SQLite 데이터베이스: 개설 강좌와 졸업 요건을 담는다.

DB 파일(app/data/planner.db)은 git 에 올리지 않는다. 처음 연결할 때 테이블을 만들고,
비어 있으면 app/data 의 원본 파일(courses.json, requirements.json, 없으면 샘플)로 채운다.
"""

import json
import os
import sqlite3
import uuid
from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.schemas import Course, GraduationRequirement, Meeting, RequiredCourse

DATA_DIR = Path(__file__).parent / "data"

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- 개설 강좌 (분반 단위)
CREATE TABLE IF NOT EXISTS courses (
    id            INTEGER PRIMARY KEY,
    year          INTEGER NOT NULL,
    semester      TEXT    NOT NULL,
    grade         TEXT,
    category      TEXT    NOT NULL,
    college       TEXT,
    department    TEXT,
    course_id     TEXT    NOT NULL,   -- 강좌번호 (교과목코드-분반)
    course_code   TEXT    NOT NULL,   -- 교과목코드
    section       TEXT,
    name          TEXT    NOT NULL,
    credits       REAL    NOT NULL,
    lecture_hours REAL,
    lab_hours     REAL,
    professor     TEXT,
    time_raw      TEXT,
    building      TEXT,
    room          TEXT,
    capacity      INTEGER,
    enrolled      INTEGER,
    UNIQUE (year, semester, course_id)
);
CREATE INDEX IF NOT EXISTS idx_courses_code       ON courses (course_code);
CREATE INDEX IF NOT EXISTS idx_courses_category   ON courses (category);
CREATE INDEX IF NOT EXISTS idx_courses_department ON courses (department);

-- 강좌별 수업 시간. 한 강좌가 주 2회면 두 줄이다.
CREATE TABLE IF NOT EXISTS meetings (
    id         INTEGER PRIMARY KEY,
    course_pk  INTEGER NOT NULL REFERENCES courses (id) ON DELETE CASCADE,
    day        TEXT    NOT NULL,      -- 월 화 수 목 금 토 일
    start_time TEXT    NOT NULL,      -- HH:MM
    end_time   TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_meetings_course ON meetings (course_pk);

-- 졸업 요건: 학과와 입학연도마다 하나
CREATE TABLE IF NOT EXISTS programs (
    id             INTEGER PRIMARY KEY,
    department     TEXT    NOT NULL,
    admission_year INTEGER NOT NULL,
    total_credits  REAL    NOT NULL,
    UNIQUE (department, admission_year)
);

-- 영역(교과구분)별 최소 학점
CREATE TABLE IF NOT EXISTS credit_requirements (
    id          INTEGER PRIMARY KEY,
    program_id  INTEGER NOT NULL REFERENCES programs (id) ON DELETE CASCADE,
    category    TEXT    NOT NULL,
    min_credits REAL    NOT NULL,
    UNIQUE (program_id, category)
);

-- 꼭 들어야 하는 과목
CREATE TABLE IF NOT EXISTS required_courses (
    id          INTEGER PRIMARY KEY,
    program_id  INTEGER NOT NULL REFERENCES programs (id) ON DELETE CASCADE,
    course_code TEXT    NOT NULL,
    name        TEXT    NOT NULL,
    UNIQUE (program_id, course_code)
);
"""

COURSE_COLUMNS = [
    "year", "semester", "grade", "category", "college", "department", "course_id",
    "course_code", "section", "name", "credits", "lecture_hours", "lab_hours",
    "professor", "time_raw", "building", "room", "capacity", "enrolled",
]

_ready: set[str] = set()


def db_path() -> Path:
    """DB 파일 위치. 환경변수 PLANNER_DB 로 바꿀 수 있다 (테스트, 배포용)."""
    return Path(os.environ.get("PLANNER_DB") or DATA_DIR / "planner.db")


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """DB 에 연결한다. 블록이 정상적으로 끝나면 저장하고, 오류가 나면 되돌린다."""
    path = db_path()
    first_use = str(path) not in _ready or not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        if first_use:
            connection.executescript(SCHEMA)
            _seed(connection)
            connection.commit()
            _ready.add(str(path))
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def _seed(connection: sqlite3.Connection) -> None:
    """비어 있는 테이블을 원본 파일로 채운다. 실제 파일이 없으면 가짜 샘플을 쓴다."""
    if connection.execute("SELECT 1 FROM courses LIMIT 1").fetchone() is None:
        real = DATA_DIR / "courses.json"
        source = real if real.exists() else DATA_DIR / "courses.sample.json"
        if source.exists():
            items = json.loads(source.read_text(encoding="utf-8"))
            replace_courses(connection, [Course(**item) for item in items], sample=source != real)

    if connection.execute("SELECT 1 FROM programs LIMIT 1").fetchone() is None:
        real = DATA_DIR / "requirements.json"
        source = real if real.exists() else DATA_DIR / "requirements.sample.json"
        if source.exists():
            items = json.loads(source.read_text(encoding="utf-8"))
            replace_requirements(
                connection, [GraduationRequirement(**item) for item in items], sample=source != real
            )


def get_meta(connection: sqlite3.Connection, key: str) -> str | None:
    row = connection.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def _set_meta(connection: sqlite3.Connection, key: str, value: str) -> None:
    connection.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) "
        "ON CONFLICT (key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


# ---------- 개설 강좌 ----------


def replace_courses(connection: sqlite3.Connection, courses: list[Course], sample: bool = False) -> int:
    """강좌를 넣는다. 같은 연도·학기의 기존 강좌는 새 것으로 바꾼다.

    가짜 샘플과 실제 데이터는 섞지 않는다. 샘플이 들어 있던 DB 에 실제 데이터를 넣으면
    샘플을 모두 지우고 넣는다.
    """
    unique = {(course.year, course.semester, course.course_id): course for course in courses}
    if sample or get_meta(connection, "courses_sample") == "1":
        connection.execute("DELETE FROM courses")
    else:
        for year, semester in {key[:2] for key in unique}:
            connection.execute("DELETE FROM courses WHERE year = ? AND semester = ?", (year, semester))

    placeholders = ", ".join("?" for _ in COURSE_COLUMNS)
    for course in unique.values():
        cursor = connection.execute(
            f"INSERT INTO courses ({', '.join(COURSE_COLUMNS)}) VALUES ({placeholders})",
            [getattr(course, column) for column in COURSE_COLUMNS],
        )
        connection.executemany(
            "INSERT INTO meetings (course_pk, day, start_time, end_time) VALUES (?, ?, ?, ?)",
            [(cursor.lastrowid, m.day, m.start, m.end) for m in course.meetings],
        )
    _set_meta(connection, "courses_sample", "1" if sample else "0")
    # 강좌가 바뀔 때마다 새 표식을 찍는다. 읽어 둔 강좌가 아직 최신인지 이것으로 판단한다.
    _set_meta(connection, "courses_version", uuid.uuid4().hex)
    return len(unique)


def fetch_courses(
    connection: sqlite3.Connection,
    q: str | None = None,
    category: str | None = None,
    department: str | None = None,
) -> list[Course]:
    """강좌를 읽는다. q 는 과목명이나 교과목코드의 일부."""
    where, values = [], []
    if q:
        where.append("(name LIKE ? OR course_code LIKE ?)")
        values += [f"%{q}%", f"%{q}%"]
    if category:
        where.append("category = ?")
        values.append(category)
    if department:
        where.append("department = ?")
        values.append(department)
    clause = f"WHERE {' AND '.join(where)}" if where else ""

    rows = connection.execute(
        f"SELECT * FROM courses {clause} ORDER BY year, semester, course_id", values
    ).fetchall()
    meetings: dict[int, list[Meeting]] = defaultdict(list)
    for row in connection.execute(
        "SELECT course_pk, day, start_time, end_time FROM meetings ORDER BY id"
    ):
        meetings[row["course_pk"]].append(
            Meeting(day=row["day"], start=row["start_time"], end=row["end_time"])
        )
    return [
        Course(**{column: row[column] for column in COURSE_COLUMNS}, meetings=meetings[row["id"]])
        for row in rows
    ]


# ---------- 졸업 요건 ----------


def replace_requirements(
    connection: sqlite3.Connection, items: list[GraduationRequirement], sample: bool = False
) -> int:
    """졸업 요건을 넣는다. 같은 학과·입학연도의 기존 요건은 새 것으로 바꾼다."""
    if sample or get_meta(connection, "requirements_sample") == "1":
        connection.execute("DELETE FROM programs")
    for item in items:
        connection.execute(
            "DELETE FROM programs WHERE department = ? AND admission_year = ?",
            (item.department, item.admission_year),
        )
        cursor = connection.execute(
            "INSERT INTO programs (department, admission_year, total_credits) VALUES (?, ?, ?)",
            (item.department, item.admission_year, item.total_credits),
        )
        connection.executemany(
            "INSERT INTO credit_requirements (program_id, category, min_credits) VALUES (?, ?, ?)",
            [(cursor.lastrowid, category, credits) for category, credits in item.credits.items()],
        )
        connection.executemany(
            "INSERT OR IGNORE INTO required_courses (program_id, course_code, name) VALUES (?, ?, ?)",
            [(cursor.lastrowid, course.course_code, course.name) for course in item.required_courses],
        )
    _set_meta(connection, "requirements_sample", "1" if sample else "0")
    return len(items)


def fetch_requirements(
    connection: sqlite3.Connection,
    department: str | None = None,
    admission_year: int | None = None,
) -> list[GraduationRequirement]:
    where, values = [], []
    if department:
        where.append("department = ?")
        values.append(department)
    if admission_year:
        where.append("admission_year = ?")
        values.append(admission_year)
    clause = f"WHERE {' AND '.join(where)}" if where else ""

    result = []
    for program in connection.execute(
        f"SELECT * FROM programs {clause} ORDER BY department, admission_year", values
    ).fetchall():
        credits = {
            row["category"]: row["min_credits"]
            for row in connection.execute(
                "SELECT category, min_credits FROM credit_requirements WHERE program_id = ? ORDER BY id",
                (program["id"],),
            )
        }
        required = [
            RequiredCourse(course_code=row["course_code"], name=row["name"])
            for row in connection.execute(
                "SELECT course_code, name FROM required_courses WHERE program_id = ? ORDER BY id",
                (program["id"],),
            )
        ]
        result.append(
            GraduationRequirement(
                department=program["department"],
                admission_year=program["admission_year"],
                total_credits=program["total_credits"],
                credits=credits,
                required_courses=required,
            )
        )
    return result


def counts(connection: sqlite3.Connection) -> dict[str, int | bool]:
    """DB 에 무엇이 얼마나 들어 있는지."""
    def count(table: str) -> int:
        return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    return {
        "courses": count("courses"),
        "meetings": count("meetings"),
        "programs": count("programs"),
        "credit_requirements": count("credit_requirements"),
        "required_courses": count("required_courses"),
        "courses_sample": get_meta(connection, "courses_sample") != "0",
        "requirements_sample": get_meta(connection, "requirements_sample") != "0",
    }
