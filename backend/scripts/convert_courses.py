"""학교 시간표 조회 화면에서 복사한 표(엑셀/CSV)를 courses.json 으로 바꾼다.

사용법 (backend 폴더에서, 가상환경을 켠 상태로):

    python -m scripts.convert_courses 내려받은파일.xlsx
    python -m scripts.convert_courses 내려받은파일.csv -o app/data/courses.json

지원 형식: .xlsx, .csv, .tsv, .txt(탭 구분)
첫 줄(또는 위쪽 몇 줄 안)에 화면과 같은 열 제목이 있어야 한다.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

from app.schemas import Course
from app.services.course_time import parse_meetings

# 화면의 열 제목 -> 내부 이름. 띄어쓰기는 무시하고 비교한다.
COLUMNS = {
    "개설연도": "year",
    "개설학기": "semester",
    "학년": "grade",
    "교과구분": "category",
    "개설대학": "college",
    "개설학과": "department",
    "강좌번호": "course_id",
    "교과목명": "name",
    "학점": "credits",
    "강의": "lecture_hours",
    "실습": "lab_hours",
    "담당교수": "professor",
    "강의시간": "period_codes",
    "강의시간(실제시간)": "real_time",
    "강의실": "building",
    "호실번호": "room",
    "수강정원": "capacity",
    "수강신청": "enrolled",
}
REQUIRED = ["course_id", "name", "credits"]


def read_rows(path: Path) -> list[list[str]]:
    """파일을 읽어 '줄 -> 칸' 의 2차원 목록으로 돌려준다."""
    suffix = path.suffix.lower()
    if suffix == ".xlsx":
        from openpyxl import load_workbook

        sheet = load_workbook(path, read_only=True, data_only=True).active
        return [
            ["" if cell is None else str(cell).strip() for cell in row]
            for row in sheet.iter_rows(values_only=True)
        ]

    delimiter = "," if suffix == ".csv" else "\t"
    for encoding in ("utf-8-sig", "cp949"):  # cp949: 한글 엑셀이 저장하는 CSV
        try:
            with path.open(encoding=encoding, newline="") as file:
                return [
                    [cell.strip() for cell in row]
                    for row in csv.reader(file, delimiter=delimiter)
                ]
        except UnicodeDecodeError:
            continue
    raise SystemExit(f"파일 글자 인코딩을 읽을 수 없습니다: {path}")


def find_header(rows: list[list[str]]) -> tuple[int, dict[str, int]]:
    """열 제목이 있는 줄을 찾아 (줄 번호, {내부 이름: 칸 번호}) 를 돌려준다."""
    for index, row in enumerate(rows[:10]):
        mapping: dict[str, int] = {}
        for position, title in enumerate(row):
            key = COLUMNS.get(title.replace(" ", "").replace("\n", ""))
            if key and key not in mapping:
                mapping[key] = position
        if all(key in mapping for key in REQUIRED):
            return index, mapping
    raise SystemExit(
        "열 제목 줄을 찾지 못했습니다. '강좌번호', '교과목명', '학점' 열이 있어야 합니다."
    )


def _text(value: str) -> str | None:
    return value or None


def _number(value: str) -> float | None:
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return None


def _integer(value: str) -> int | None:
    number = _number(value)
    return None if number is None else int(number)


def convert(rows: list[list[str]]) -> tuple[list[Course], list[str]]:
    """표를 Course 목록으로 바꾼다. 문제가 있는 줄은 경고 목록에 담는다."""
    header_index, columns = find_header(rows)
    courses: dict[tuple[int, str, str], Course] = {}
    warnings: list[str] = []

    for line_number, row in enumerate(rows[header_index + 1 :], start=header_index + 2):

        def cell(key: str) -> str:
            position = columns.get(key)
            return row[position] if position is not None and position < len(row) else ""

        course_id = cell("course_id")
        if not course_id:
            continue  # 빈 줄

        credits = _number(cell("credits"))
        if not cell("name") or credits is None:
            warnings.append(f"{line_number}번째 줄 건너뜀: 교과목명 또는 학점이 없음 ({course_id})")
            continue

        code, _, section = course_id.partition("-")
        period_codes, real_time = cell("period_codes"), cell("real_time")
        meetings = parse_meetings(real_time, period_codes)
        if not meetings and (period_codes or real_time):
            warnings.append(
                f"{line_number}번째 줄 시간 해석 실패 ({course_id}): "
                f"{real_time or period_codes!r}"
            )

        course = Course(
            year=_integer(cell("year")) or 0,
            semester=cell("semester"),
            grade=_text(cell("grade")),
            category=cell("category"),
            college=_text(cell("college")),
            department=_text(cell("department")),
            course_id=course_id,
            course_code=code,
            section=_text(section),
            name=cell("name"),
            credits=credits,
            lecture_hours=_number(cell("lecture_hours")),
            lab_hours=_number(cell("lab_hours")),
            professor=_text(cell("professor")),
            time_raw=_text(real_time or period_codes),
            meetings=meetings,
            building=_text(cell("building")),
            room=_text(cell("room")),
            capacity=_integer(cell("capacity")),
            enrolled=_integer(cell("enrolled")),
        )
        key = (course.year, course.semester, course.course_id)
        if key in courses:
            warnings.append(f"{line_number}번째 줄 중복 강좌, 나중 것으로 덮어씀 ({course_id})")
        courses[key] = course

    return list(courses.values()), warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="시간표 엑셀/CSV 를 courses.json 으로 변환")
    parser.add_argument("input", type=Path, help="변환할 파일 (.xlsx, .csv, .tsv, .txt)")
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("app/data/courses.json"), help="저장할 JSON 경로"
    )
    args = parser.parse_args()

    courses, warnings = convert(read_rows(args.input))
    args.output.write_text(
        json.dumps([course.model_dump() for course in courses], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    without_time = sum(1 for course in courses if not course.meetings)
    print(f"강좌 {len(courses)}개 저장: {args.output}")
    print(f"시간이 없는 강좌 {without_time}개, 경고 {len(warnings)}건")
    for warning in warnings:
        print(f"  - {warning}", file=sys.stderr)


if __name__ == "__main__":
    main()
