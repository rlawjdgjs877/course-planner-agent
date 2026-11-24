"""졸업자가진단 응답 읽기. 응답 모양은 실제 학교 화면에서 칸 이름만 확인해 만든 가짜 값이다."""

from app.services import knu_graduation as g

STUDENT = {
    "success": True,
    "data": [
        {
            "grade": "3",
            "pstnDprtnNm": "IT대학 컴퓨터학부 심화컴퓨팅전공",
            "stdno": "2023000000",
            "schrsDtalSttnm": "재학",
            "admsnSctinNm": "신입학",
            "cmpsNm": "대구캠퍼스",
            "gpa": "3.8",
            "totGrCrdit": "75",
            "kornNm": "홍길동",
            "brthd": "20040101",
            "mblph": "010-0000-0000",
            "email": "a@b.c",
            "prtecBscdd": "대구",
        }
    ],
}
DIAGNOSIS = {
    "success": True,
    "data": {
        "admsnYear": "2022",
        "crsdcApptnYear": "2022",
        "complSmstrCnt": "5",
        "mthmcScncExmptYn": "N",
        "tcTrgprYn": "N",
        "cmbdcTpnm": "-",
        "cmbdcDprtnNm": "-",
    },
}
DETAIL = {
    "success": True,
    "data": [
        {"univGrdtnAssssStnnm": "총학점", "sbjetSctin": None, "sndrdCrdit": "140", "complCrdit": "75", "stgrCrdit2": "75", "sffcnYn": "N"},
        {"univGrdtnAssssStnnm": "첨성인기초", "sbjetSctin": "교양", "sndrdCrdit": "18", "complCrdit": "18", "stgrCrdit2": "18", "sffcnYn": "Y"},
        {"univGrdtnAssssStnnm": "첨성인핵심인문", "sbjetSctin": "교양", "sndrdCrdit": "6", "complCrdit": "3", "stgrCrdit2": "0", "trmssStcuCrdit": "3", "sffcnYn": "N"},
        {"univGrdtnAssssStnnm": "첨성인핵심자연", "sbjetSctin": "교양", "sndrdCrdit": "6", "complCrdit": "0", "stgrCrdit2": "0", "sffcnYn": "N"},
        {"univGrdtnAssssStnnm": "전공필수", "sbjetSctin": "전공", "mltmjTpnm": "주전공", "sndrdCrdit": "30", "complCrdit": "21", "sffcnYn": "N"},
    ],
}
ESSENTIAL = {
    "success": True,
    "data": [
        {"sbjetCd": "COMP0204", "sbjetNm": "자료구조", "crdit": "3", "complYear": "2023", "gradsGradCd": "A0"},
        {"sbjetCd": "COMP0312", "sbjetNm": "운영체제", "crdit": "3", "complYear": "2026", "gradsGradCd": None},
        {"sbjetCd": "COMP0411", "sbjetNm": "종합설계프로젝트1", "crdit": "3", "complYear": None, "gradsGradCd": None},
    ],
}


def test_student_keeps_only_needed_fields():
    student = g.extract_student(STUDENT)
    assert student.grade == 3
    assert student.track == "advanced"
    assert student.admission_year == "2023"  # 진단 기본값이 없으면 학번 앞 4자리
    assert student.status == "재학" and student.admission_type == "신입학"
    dumped = student.model_dump_json()
    for secret in ("홍길동", "20040101", "010-0000-0000", "a@b.c", "2023000000", "대구\""):
        assert secret not in dumped


def test_diagnosis_overrides_admission_year():
    student = g.extract_student(STUDENT, g.extract_diagnosis(DIAGNOSIS))
    assert student.admission_year == "2022"
    assert student.curriculum_year == "2022"
    assert student.semesters == 5
    assert student.other_major is None
    # 순서가 바뀌어도 같은 결과
    again = g.extract_diagnosis(DIAGNOSIS, g.extract_student(STUDENT))
    assert again.admission_year == "2022" and again.grade == 3


def test_requirements_and_shortage():
    rows = g.extract_requirements(DETAIL)
    by = {r.name: r for r in rows}
    # 수강 중 3학점은 이수로 치지 않는다 (성적이 나온 0학점 기준)
    assert by["첨성인핵심인문"].earned == 0 and by["첨성인핵심인문"].shortage == 6
    assert by["첨성인핵심인문"].area == "인문"
    assert by["첨성인기초"].satisfied is True
    assert by["전공필수"].area is None
    assert g.shortage_areas(rows) == ["인문", "자연"]


def test_required_courses_state():
    states = {c.name: c.state for c in g.extract_required_courses(ESSENTIAL)}
    assert states == {"자료구조": "done", "운영체제": "missing", "종합설계프로젝트1": "missing"}  # 수강 중은 미이수


def test_student_number_from_transcript_or_request():
    assert g.student_number({"data": [{"stdno": "2023000000", "sbjetCd": "A"}]}) == "2023000000"
    assert g.student_number({"data": []}, '{"search":{"stdno":"2024111111"}}') == "2024111111"
    assert g.student_number({"data": []}, "not json") is None


def test_bad_payload_raises():
    import pytest

    with pytest.raises(ValueError):
        g.extract_requirements({"data": None})


def test_satisfied_is_recomputed_without_courses_in_progress():
    rows = g.extract_requirements({"data": [
        {"univGrdtnAssssStnnm": "첨성인핵심자연", "sbjetSctin": "교양", "sndrdCrdit": "6", "complCrdit": "6",
         "stgrCrdit2": "3", "trmssStcuCrdit": "3", "sffcnYn": "Y"},
    ]})
    assert rows[0].earned == 3 and rows[0].satisfied is False and rows[0].shortage == 3


def test_transcript_skips_courses_without_grade_yet():
    from app.services.knu_transcript import extract_courses

    courses, _ = extract_courses({"data": [
        {"sbjetCd": "A1", "sbjetNm": "들은 과목", "crdit": "3", "gradsGradCd": "A0"},
        {"sbjetCd": "A2", "sbjetNm": "수강 중", "crdit": "3", "gradsGradCd": None},
        {"sbjetCd": "A3", "sbjetNm": "성적 칸 없는 직접 입력", "crdit": "3"},
    ]})
    assert [c.code for c in courses] == ["A1", "A3"]
