"""데이터베이스에 자료를 넣는다.

사용법 (backend 폴더에서, 가상환경을 켠 상태로):

    python -m scripts.import_data courses 시간표.xlsx        강좌 넣기 (.xlsx .csv .tsv .txt .json)
    python -m scripts.import_data requirements 요건.json     졸업 요건 넣기
    python -m scripts.import_data offerings ../frontend/data/course-sources   학교 조회 응답(JSON) 폴더나 파일 넣기
    python -m scripts.import_data status                     지금 들어 있는 자료 확인

강좌는 같은 연도·학기의 기존 강좌를 새 것으로 바꾼다. 가짜 샘플이 들어 있었다면 지우고 넣는다.
넣은 자료는 app/data/courses.json, requirements.json 으로도 저장한다. DB 파일은 git 에 올리지
않으므로, 팀원은 이 JSON 파일을 받아 서버를 켜면 같은 DB 가 만들어진다.
"""

import argparse
import json
import sys
from pathlib import Path

from app import db
from app.schemas import Course, GraduationRequirement
from app.services.knu_offerings import courses_from_school_json
from scripts.convert_courses import convert, read_rows


def read_courses(path: Path) -> tuple[list[Course], list[str]]:
    if path.suffix.lower() == ".json":
        return [Course(**item) for item in json.loads(path.read_text(encoding="utf-8"))], []
    return convert(read_rows(path))


def save_json(name: str, items: list) -> Path:
    path = db.DATA_DIR / name
    path.write_text(
        json.dumps([item.model_dump() for item in items], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def print_status() -> None:
    with db.connect() as connection:
        status = db.counts(connection)
    print(f"DB 파일: {db.db_path()}")
    print(f"강좌 {status['courses']}개, 수업 시간 {status['meetings']}건"
          + (" (가짜 샘플)" if status["courses_sample"] else ""))
    print(f"졸업 요건 {status['programs']}개 학과·입학연도, 영역별 학점 {status['credit_requirements']}건, "
          f"필수 과목 {status['required_courses']}건"
          + (" (가짜 샘플)" if status["requirements_sample"] else ""))


def main() -> None:
    parser = argparse.ArgumentParser(description="데이터베이스에 자료 넣기")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (("courses", "강좌 넣기"), ("requirements", "졸업 요건 넣기")):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("file", type=Path, help="넣을 파일")
    offerings = commands.add_parser("offerings", help="학교 수업시간표 조회 응답(JSON) 넣기")
    offerings.add_argument("paths", type=Path, nargs="+", help="JSON 파일이나 그 파일들이 든 폴더")
    commands.add_parser("status", help="들어 있는 자료 확인")
    args = parser.parse_args()

    if args.command == "courses":
        courses, warnings = read_courses(args.file)
        if not courses:
            raise SystemExit("넣을 강좌가 없습니다. 파일 내용을 확인하세요.")
        with db.connect() as connection:
            count = db.replace_courses(connection, courses)
            saved = db.fetch_courses(connection)
        print(f"강좌 {count}개를 넣었습니다. 원본 저장: {save_json('courses.json', saved)}")
        for warning in warnings:
            print(f"  - {warning}", file=sys.stderr)

    elif args.command == "offerings":
        files = [f for path in args.paths for f in (sorted(path.glob("*.json")) if path.is_dir() else [path])]
        courses, warnings = courses_from_school_json(files)
        if not courses:
            raise SystemExit("넣을 강좌가 없습니다. 파일 경로를 확인하세요.")
        with db.connect() as connection:
            count = db.replace_courses(connection, courses)
            saved = db.fetch_courses(connection)
        print(f"파일 {len(files)}개에서 강좌 {count}개를 넣었습니다. 원본 저장: {save_json('courses.json', saved)}")
        for warning in warnings:
            print(f"  - {warning}", file=sys.stderr)

    elif args.command == "requirements":
        items = [
            GraduationRequirement(**item)
            for item in json.loads(args.file.read_text(encoding="utf-8"))
        ]
        with db.connect() as connection:
            count = db.replace_requirements(connection, items)
            saved = db.fetch_requirements(connection)
        print(f"졸업 요건 {count}개를 넣었습니다. 원본 저장: {save_json('requirements.json', saved)}")

    print_status()


if __name__ == "__main__":
    main()
