"""개설 강좌와 졸업 요건을 데이터베이스에서 읽는다."""

import json
from pathlib import Path

from app import db
from app.schemas import Course, GraduationRequirement

# 시간표를 짤 때마다 전체 강좌를 다시 읽지 않도록, 강좌가 바뀌기 전까지는 읽어 둔 것을 쓴다.
# 강좌를 넣을 때마다 DB 에 새 표식(courses_version)이 찍히므로 그것으로 바뀌었는지 안다.
_cache: dict[tuple[str, str | None], list[Course]] = {}


def using_sample_data() -> bool:
    """실제 강좌 데이터가 아직 없어 가짜 샘플을 쓰고 있는지."""
    with db.connect() as connection:
        return db.get_meta(connection, "courses_sample") != "0"


def load_courses(path: Path | None = None) -> list[Course]:
    """전체 강좌. path 를 주면 DB 대신 그 JSON 파일을 읽는다 (테스트, 변환 확인용)."""
    if path is not None:
        return [Course(**item) for item in json.loads(path.read_text(encoding="utf-8"))]

    with db.connect() as connection:
        key = (str(db.db_path()), db.get_meta(connection, "courses_version"))
        if key not in _cache:
            _cache.clear()
            _cache[key] = db.fetch_courses(connection)
        return _cache[key]


def search_courses(
    q: str | None = None, category: str | None = None, department: str | None = None
) -> list[Course]:
    """조건에 맞는 강좌만 읽는다."""
    with db.connect() as connection:
        return db.fetch_courses(connection, q=q, category=category, department=department)


def load_requirements(
    department: str | None = None, admission_year: int | None = None
) -> tuple[list[GraduationRequirement], bool]:
    """졸업 요건과, 그것이 가짜 샘플인지 여부."""
    with db.connect() as connection:
        items = db.fetch_requirements(connection, department, admission_year)
        return items, db.get_meta(connection, "requirements_sample") != "0"
