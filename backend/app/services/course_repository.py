"""개설 강좌 데이터를 파일에서 읽는다."""

import json
from pathlib import Path

from app.schemas import Course

DATA_DIR = Path(__file__).parent.parent / "data"
REAL_DATA = DATA_DIR / "courses.json"
SAMPLE_DATA = DATA_DIR / "courses.sample.json"


def using_sample_data() -> bool:
    """실제 데이터(courses.json)가 아직 없어 가짜 샘플 데이터를 쓰고 있는지."""
    return not REAL_DATA.exists()


def load_courses(path: Path | None = None) -> list[Course]:
    """courses.json 을 읽는다. 아직 없으면 가짜 샘플 데이터(courses.sample.json)를 쓴다."""
    if path is None:
        path = SAMPLE_DATA if using_sample_data() else REAL_DATA
    return [Course(**item) for item in json.loads(path.read_text(encoding="utf-8"))]
