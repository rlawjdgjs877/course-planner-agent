"""학교 '수업시간표 조회' 응답(JSON)을 개설 강좌 목록으로 바꾼다.

프론트엔드 팀이 모아 둔 frontend/data/course-sources/*.json 이 이 형식이다.
파일 하나가 자료 하나(트랙 또는 교양 영역)이고, 파일 이름이 자료 이름(source)이 된다.
같은 분반이 여러 파일에 다른 이수구분·학년으로 나오면 한 강좌로 합치고 listings 에 모두 남긴다.
"""

import json
from pathlib import Path

from app.schemas import Course, CourseListing
from app.services.course_time import parse_meetings

# 기본 이수구분을 정할 때 먼저 보는 자료. 트랙이 정해지면 시간표를 짤 때 그 트랙 기준으로 바꾼다.
SOURCE_PRIORITY = ["computing", "advanced", "ai", "research", "platform", "global"]


def _text(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _number(value: object) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _integer(value: object) -> int | None:
    number = _number(value)
    return None if number is None else int(number)


def read_rows(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError(f"{path.name}: data 배열이 없습니다.")
    return [row for row in rows if isinstance(row, dict)]


def courses_from_school_json(paths: list[Path]) -> tuple[list[Course], list[str]]:
    """여러 응답 파일을 강좌 목록으로 합친다. (강좌 목록, 경고 목록)"""
    grouped: dict[tuple, list[tuple[str, dict]]] = {}
    warnings: list[str] = []
    for path in sorted(paths):
        source = path.stem
        for row in read_rows(path):
            course_id = _text(row.get("crseNo"))
            if not course_id or not _text(row.get("sbjetNm")) or _number(row.get("crdit")) is None:
                warnings.append(f"{path.name}: 강좌번호, 과목명, 학점 중 빠진 행을 건너뛰었습니다 ({course_id}).")
                continue
            key = (_integer(row.get("estblYear")) or 0, _text(row.get("estblSmstrSctnm")) or "", course_id)
            grouped.setdefault(key, []).append((source, row))

    courses: list[Course] = []
    for (year, semester, course_id), rows in grouped.items():
        listings: list[CourseListing] = []
        for source, row in rows:
            listing = CourseListing(
                source=source,
                category=_text(row.get("sbjetSctnm")) or "미분류",
                grade=_text(row.get("estblGrade")),
                department=_text(row.get("estblDprtnNm")),
            )
            if listing not in listings:
                listings.append(listing)
        listings.sort(key=lambda x: SOURCE_PRIORITY.index(x.source) if x.source in SOURCE_PRIORITY else 99)

        first = rows[0][1]
        real_time, period_codes = _text(first.get("lssnsRealTimeInfo")), _text(first.get("lssnsTimeInfo"))
        times = {(_text(r.get("lssnsRealTimeInfo")), _text(r.get("lssnsTimeInfo"))) for _, r in rows}
        if len(times) > 1:
            warnings.append(f"{course_id}: 자료마다 수업 시간이 달라 첫 번째 값을 썼습니다.")
        meetings = parse_meetings(real_time, period_codes)
        if not meetings and (real_time or period_codes):
            warnings.append(f"{course_id}: 수업 시간을 해석하지 못했습니다 ({real_time or period_codes}).")

        code = _text(first.get("sbjetCd")) or course_id.split("-")[0]
        courses.append(
            Course(
                year=year,
                semester=semester,
                grade=listings[0].grade,
                category=listings[0].category,
                college=_text(first.get("estblUnivNm")),
                department=listings[0].department,
                course_id=course_id,
                course_code=code,
                section=_text(first.get("sbjetDvnno")) or (course_id.split("-")[1] if "-" in course_id else None),
                name=_text(first.get("sbjetNm")),
                credits=_number(first.get("crdit")),
                lecture_hours=_number(first.get("thryTime")),
                lab_hours=_number(first.get("prctsTime")),
                professor=_text(first.get("totalPrfssNm")),
                time_raw=real_time or period_codes,
                meetings=meetings,
                building=_text(first.get("lctrmInfo")),
                room=_text(first.get("rmnmCd")),
                # 학교 응답의 필드 뜻은 화면 열 제목으로 짐작한 것이다 (수강정원, 수강신청 인원).
                capacity=_integer(first.get("attlcPrscpCnt")),
                enrolled=_integer(first.get("appcrCnt")),
                listings=listings,
            )
        )
    courses.sort(key=lambda course: course.course_id)
    return courses, warnings
