from pathlib import Path

from app.schemas import Meeting
from app.services.course_time import (
    courses_conflict,
    meetings_overlap,
    parse_meetings,
    parse_period_codes,
    parse_real_time,
    period_to_minutes,
)
from scripts.convert_courses import convert, read_rows

SAMPLE = Path(__file__).parent.parent / "app" / "data" / "courses.sample.csv"


def times(meetings: list[Meeting]) -> list[tuple[str, str, str]]:
    return [(m.day, m.start, m.end) for m in meetings]


def test_period_codes_follow_school_table():
    assert period_to_minutes("1A") == (9 * 60, 9 * 60 + 30)
    assert period_to_minutes("1B") == (9 * 60 + 30, 10 * 60)
    assert period_to_minutes("9B") == (17 * 60 + 30, 18 * 60)
    assert period_to_minutes("0B") == (8 * 60 + 30, 9 * 60)


def test_parse_period_codes_merges_consecutive_periods():
    assert times(parse_period_codes("월 1A,1B,2A 수 1A,1B,2A")) == [
        ("월", "09:00", "10:30"),
        ("수", "09:00", "10:30"),
    ]


def test_parse_period_codes_keeps_gap_as_separate_meetings():
    assert times(parse_period_codes("월 1A,1B 5A")) == [
        ("월", "09:00", "10:00"),
        ("월", "13:00", "13:30"),
    ]


def test_parse_real_time():
    assert times(parse_real_time("월 09:00 ~ 10:30, 수 09:00 ~ 10:30")) == [
        ("월", "09:00", "10:30"),
        ("수", "09:00", "10:30"),
    ]
    # 요일을 묶어 쓴 표기, 물결표 대신 하이픈
    assert times(parse_real_time("화,목 13:00-14:30")) == [
        ("화", "13:00", "14:30"),
        ("목", "13:00", "14:30"),
    ]


def test_parse_meetings_falls_back_to_period_codes():
    assert times(parse_meetings("", "금 1A,1B,2A,2B")) == [("금", "09:00", "11:00")]
    assert parse_meetings("", "") == []


def test_back_to_back_meetings_do_not_overlap():
    first = Meeting(day="월", start="09:00", end="10:30")
    assert not meetings_overlap(first, Meeting(day="월", start="10:30", end="12:00"))
    assert meetings_overlap(first, Meeting(day="월", start="10:00", end="11:30"))
    assert not meetings_overlap(first, Meeting(day="화", start="09:00", end="10:30"))


def test_convert_sample_file():
    courses, warnings = convert(read_rows(SAMPLE))
    by_id = {course.course_id: course for course in courses}

    assert warnings == []
    assert len(courses) == 8

    data_structures = by_id["SAMP0201-001"]
    assert data_structures.course_code == "SAMP0201"
    assert data_structures.section == "001"
    assert data_structures.credits == 3
    assert data_structures.capacity == 60
    assert times(data_structures.meetings) == [
        ("월", "09:00", "10:30"),
        ("수", "09:00", "10:30"),
    ]

    # 실제시간 열이 비어 있으면 교시 코드로 해석한다
    assert times(by_id["SAMP0101-003"].meetings) == [("금", "09:00", "11:00")]
    # 시간이 없는 원격 강좌
    assert by_id["SAMP0103-001"].meetings == []

    # 월·수 09:00~10:30 과 월·수 10:00~11:30 은 겹친다
    assert courses_conflict(data_structures, by_id["SAMP0202-001"])
    # 같은 과목의 다른 분반(화·목)은 겹치지 않는다
    assert not courses_conflict(data_structures, by_id["SAMP0201-002"])
