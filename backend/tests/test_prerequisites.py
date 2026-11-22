"""선수과목 확인과 시간표 생성기의 자동 추천 기준 (선수과목, 주말, 외국인·타 단과대 교양, 트랙 별칭)."""

import time
from pathlib import Path

import pytest

from app.schemas import Course, CourseListing, GenerateTimetableRequest, Meeting
from app.services import planner, prerequisites
from app.services.course_repository import load_courses

DATA = Path(__file__).parent.parent / "app" / "data"


def course(code, name, days=("월", "수"), start="09:00", end="10:30", category="전공선택", grade="2",
           department="컴퓨터학부", sources=("computing",), credits=3.0, section="001"):
    return Course(
        year=2026, semester="2학기", grade=grade, category=category, department=department,
        course_id=f"{code}-{section}", course_code=code, section=section, name=name, credits=credits,
        meetings=[Meeting(day=d, start=start, end=end) for d in days],
        listings=[CourseListing(source=s, category=category, grade=grade) for s in sources],
    )


CATALOG = [
    course("C100", "프로그래밍기초", ("월", "수"), "09:00", "10:30", grade="1"),
    course("C200", "자료구조", ("화", "목"), "09:00", "10:30"),
    course("C210", "시스템프로그래밍", ("월", "수"), "12:00", "13:30"),
    course("C220", "운영체제", ("화", "목"), "12:00", "13:30"),
    course("C230", "데이타통신", ("월", "수"), "15:00", "16:30"),
    course("C240", "컴퓨터망", ("화", "목"), "15:00", "16:30", grade="3"),
    course("C300", "알고리즘2", ("금",), "09:00", "12:00", grade="3"),
]


# ---------- 자료와 이름 맞추기 ----------


def test_chains_loaded_from_pdf_data():
    chains = prerequisites.load_chains()
    assert len(chains) == 19
    assert all(chain["page"] in (1, 2) for chain in chains)
    first = chains[0]
    assert first["category"] == "공통 · 프로그래밍" and first["stages"][0] == ("기초프로그래밍", "프로그래밍기초")


@pytest.mark.parametrize(
    "a, b",
    [("데이타통신", "데이터통신"), ("데이타 베이스", "데이터베이스"), ("운영체제(샘플)", "운영체제"),
     ("문제해결기반 공학연수실습(심화컴퓨터학)", "문제해결기반공학연수실습"), ("일반생명과학Ⅰ", "일반생명과학1")],
)
def test_normalize_absorbs_spelling_differences(a, b):
    assert prerequisites.normalize(a) == prerequisites.normalize(b)


def test_most_offered_computing_chain_courses_match_the_catalog():
    catalog = {prerequisites.normalize(c.name) for c in load_courses(DATA / "courses.json")}
    for name in ["자료구조", "운영체제", "시스템프로그래밍", "데이터통신", "데이터베이스", "컴퓨터망", "알고리즘2",
                 "문제해결기반공학연수실습", "클라우드컴퓨팅"]:
        assert prerequisites.normalize(name) in catalog, name


# ---------- check ----------


def test_check_previous_stage_by_name_or_code():
    assert prerequisites.check("운영체제", [], CATALOG) == [
        {"chain": "공통 · 시스템", "required": "시스템프로그래밍", "satisfied": False, "page": 1}
    ]
    assert prerequisites.check("C220", ["C210"], CATALOG)[0]["satisfied"] is True
    assert prerequisites.check("운영체제", ["시스템 프로그래밍"], CATALOG)[0]["satisfied"] is True


def test_alternatives_and_spelling_in_completed():
    # '기초프로그래밍 / 프로그래밍기초' 중 하나만 들어도 자료구조는 충족
    assert prerequisites.check("자료구조", ["C100"], CATALOG)[0]["satisfied"] is True
    assert prerequisites.check("컴퓨터망", ["데이터통신"], CATALOG)[0]["satisfied"] is True


def test_first_stage_or_unknown_course_has_no_requirement():
    assert prerequisites.check("시스템프로그래밍", [], CATALOG) == []  # 공통 · 시스템 첫 단계
    assert prerequisites.check("세계의 문화", [], CATALOG) == []


def test_track_specific_chains_apply_only_to_that_track():
    # AI · SW 사슬: 자료구조응용 → 운영체제. 인컴 학생은 둘 중 하나의 앞 단계만 들었으면 충족.
    checker = prerequisites.Checker(["자료구조응용"], CATALOG, track="ai")
    assert checker.issue("운영체제") is None
    assert prerequisites.Checker(["자료구조응용"], CATALOG, track="advanced").issue("운영체제")["missing"] == ["시스템프로그래밍"]


def test_issues_for_separates_missing_and_concurrent():
    sections = [CATALOG[2], CATALOG[3], CATALOG[5]]  # 시스템프로그래밍, 운영체제, 컴퓨터망
    issues = prerequisites.issues_for(sections, [], CATALOG)
    by_name = {issue["name"]: issue for issue in issues}
    assert set(by_name) == {"운영체제", "컴퓨터망"}
    assert by_name["운영체제"]["kind"] == "concurrent" and by_name["운영체제"]["missing"] == ["시스템프로그래밍"]
    assert by_name["컴퓨터망"]["kind"] == "missing" and by_name["컴퓨터망"]["missing"] == ["데이타통신"]
    assert prerequisites.describe(by_name["컴퓨터망"]) == "선수과목 확인: 컴퓨터망 ← 데이타통신 미이수 (선수과목 안내 1쪽)"


# ---------- 시간표 생성기 ----------


def plan(catalog=CATALOG, **body):
    defaults = dict(min_credits=0, target_credits=6, max_credits=12, track="advanced", grade=2)
    return planner.generate(GenerateTimetableRequest(**(defaults | body)), catalog)


def names(candidate):
    return {section.name for section in candidate.sections}


def test_auto_recommendation_skips_courses_without_prerequisites():
    result = plan(completed=["프로그래밍기초", "자료구조"], target_credits=12)
    for candidate in result.candidates:
        assert not names(candidate) & {"운영체제", "컴퓨터망", "알고리즘2"}
        assert candidate.prereq_issues == []
    assert any("자동 추천에서 뺐습니다" in w for w in result.warnings)


def test_must_include_without_prerequisite_is_kept_with_a_warning():
    result = plan(completed=["프로그래밍기초", "자료구조"], must_include=["운영체제"], exclude=["시스템프로그래밍"])
    assert result.status == "success"
    for candidate in result.candidates:
        assert "운영체제" in names(candidate)
        [issue] = [i for i in candidate.prereq_issues if i.name == "운영체제"]
        assert (issue.kind, issue.missing, issue.chain, issue.page) == ("missing", ["시스템프로그래밍"], "공통 · 시스템", 1)
    assert "선수과목 확인: 운영체제 ← 시스템프로그래밍 미이수 (선수과목 안내 1쪽)" in result.warnings


def test_must_include_with_prerequisite_in_same_term_is_concurrent():
    result = plan(completed=["자료구조"], must_include=["시스템프로그래밍", "운영체제"])
    [issue] = result.candidates[0].prereq_issues
    assert issue.kind == "concurrent" and issue.name == "운영체제"


def test_completed_prerequisite_allows_the_next_course():
    result = plan(completed=["자료구조", "시스템프로그래밍"], must_include=["운영체제"])
    assert all(c.prereq_issues == [] for c in result.candidates)


def test_real_catalog_second_year_advanced_student():
    catalog = load_courses(DATA / "courses.json")
    started = time.perf_counter()
    result = planner.generate(
        GenerateTimetableRequest(track="advanced", grade=2, completed=["기초프로그래밍", "자료구조"],
                                 must_include=["운영체제"]),
        catalog,
    )
    assert time.perf_counter() - started < 3
    assert result.candidates
    for candidate in result.candidates:
        flagged = {issue.name for issue in candidate.prereq_issues}
        assert flagged == {"운영체제"}  # 자동으로 고른 과목에는 선수과목 문제가 없다
    assert any(w.startswith("선수과목 확인: 운영체제 ← 시스템프로그래밍") for w in result.warnings)


# ---------- 주말, 외국인·타 단과대 교양, 학년 ----------


GE = [
    course("G1", "토요 교양", ("토",), "09:00", "12:00", category="교양", grade="*", sources=("literacy",)),
    course("G2", "Korean Language I", ("월",), "13:00", "15:00", category="교양", grade="*", department="국제처", sources=("literacy",)),
    course("G3", "외국인을 위한 한국어 문법", ("화",), "13:00", "15:00", category="교양", grade="*", department="국어국문학과", sources=("literacy",)),
    course("G4", "인문사회 기초수학", ("수",), "13:00", "15:00", category="교양", grade="1", sources=("foundation",)),
    course("G5", "세계문화의 이해", ("목",), "13:00", "15:00", category="교양", grade="*", sources=("core-humanities",)),
]


def test_weekend_and_unsuitable_ge_are_not_auto_recommended():
    result = plan(catalog=GE, completed=["x"], target_credits=12)
    assert result.candidates
    assert all(names(c) <= {"세계문화의 이해"} for c in result.candidates)
    weekend = plan(catalog=GE, completed=["x"], target_credits=12, allow_weekend=True)
    assert any("토요 교양" in names(c) for c in weekend.candidates)
    forced = plan(catalog=GE, must_include=["토요 교양", "Korean Language I"])
    assert all({"토요 교양", "Korean Language I"} <= names(c) for c in forced.candidates)


def test_not_recommended_reasons():
    assert planner.not_recommended(GE[0], allow_weekend=False) == "토·일 수업"
    assert planner.not_recommended(GE[0]) is None  # 기본값은 예전과 같다
    assert planner.not_recommended(GE[1]) == "외국인 대상 교양"
    assert planner.not_recommended(GE[2]) == "외국인 대상 교양"
    assert planner.not_recommended(GE[3]) == "다른 단과대 학생용 교양"
    assert planner.not_recommended(GE[4]) is None


def test_science_basics_and_lower_grade_ge_are_penalized():
    chem = course("G6", "화학 II", category="교양", grade="1", sources=("foundation",))
    listed = course("G7", "일반생명과학Ⅰ", category="교양", grade="1", sources=("computing", "core-natural"))
    assert planner.fit_bonus(chem, "advanced", 2) <= -6
    assert planner.fit_bonus(listed, "advanced", 2) > -6  # 컴학 자료에 있으면 감점하지 않는다
    ge = course("G8", "교양X", category="교양", grade="1", sources=("literacy",))
    assert planner.fit_bonus(ge, "advanced", 3) == -0.5


# ---------- 트랙 별칭 ----------


@pytest.mark.parametrize(
    "value, expected",
    [("advanced", "advanced"), ("deep", "advanced"), ("심컴", "advanced"), ("심화컴퓨팅전공", "advanced"),
     ("AI", "ai"), ("인공지능컴퓨팅전공", "ai"), ("플랫폼SW·데이터과학전공", "platform"), ("글솦", "global"),
     ("unknown", None), (None, None)],
)
def test_track_aliases(value, expected):
    assert planner.resolve_track(value) == expected


def test_alias_track_has_no_unknown_warning():
    result = plan(track="deep")
    assert result.applied["track"] == "advanced"
    assert not any("알 수 없는 트랙" in w for w in result.warnings)
