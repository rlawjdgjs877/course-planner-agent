"""학교 '졸업자가진단' 화면 응답에서 학생 정보와 교과구분별 이수 현황을 뽑는다.

학생 기본정보 응답(selectStudentInfoUdc)에는 이름, 생년월일, 연락처, 주소 같은 개인정보가 함께 온다.
여기서는 필요한 칸(학년, 소속, 학적, 입학 구분 등)만 읽고 나머지는 보지도, 남기지도 않는다.
학번은 졸업자가진단 조회와 입학 연도(앞 4자리) 추정에만 쓰고 결과에 남기지 않는다.
"""

import json
import re

from app.schemas import Certification, CreditStatus, EssentialCourse, ImportedStudent

TRACKS = {  # 소속 이름에 들어 있는 전공 → 화면의 전공 id
    "심화컴퓨팅": "advanced",
    "인공지능컴퓨팅": "ai",
    "첨단컴퓨팅": "research",
    "플랫폼": "platform",
    "글로벌": "global",
}


def _text(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _number(value: object) -> float | None:
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _rows(payload: object) -> list[dict]:
    rows = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(rows, dict):
        rows = [rows]
    if not isinstance(rows, list):
        raise ValueError("응답에 data 배열이 없습니다.")
    return [row for row in rows if isinstance(row, dict)]


def student_number(transcript: object, request_body: str | None = None) -> str | None:
    """이수성적 응답(행의 stdno)이나 그 요청 본문(search.stdno)에서 학번을 찾는다. 졸업자가진단 조회에만 쓴다."""
    rows = transcript.get("data") if isinstance(transcript, dict) else None
    for row in rows if isinstance(rows, list) else []:
        if isinstance(row, dict) and re.fullmatch(r"\d{6,12}", _text(row.get("stdno"))):
            return _text(row.get("stdno"))
    try:
        body = json.loads(request_body or "")
        found = _text((body.get("search") or {}).get("stdno")) if isinstance(body, dict) else ""
    except (ValueError, AttributeError):
        found = ""
    return found if re.fullmatch(r"\d{6,12}", found) else None


def track_of(department: str) -> str | None:
    compact = department.replace(" ", "")
    return next((track for key, track in TRACKS.items() if key in compact), None)


def _year(value: object) -> str | None:
    text = _text(value)[:4]
    return text if re.fullmatch(r"(19|20)\d{2}", text) else None


def _flag(value: object) -> bool | None:
    text = _text(value).upper()
    return True if text == "Y" else False if text == "N" else None


def _short(value: object, limit: int = 40) -> str | None:
    text = _text(value)
    return text[:limit] if text and text != "-" else None


def extract_student(payload: object, base: ImportedStudent | None = None) -> ImportedStudent:
    """학생 기본정보 응답에서 학년, 소속, 학적 상태, 입학 구분, 평점, 총 취득학점만 꺼낸다.

    이름·생년월일·주민번호·연락처·주소 칸은 읽지 않는다. 학번은 입학 연도를 모를 때 앞 4자리만 쓴다.
    """
    rows = _rows(payload)
    if not rows:
        raise ValueError("학생 정보가 비어 있습니다.")
    row = rows[0]
    grade = _text(row.get("grade"))
    department = _text(row.get("pstnDprtnNm"))
    student = (base or ImportedStudent()).model_copy()
    student.grade = int(grade) if grade.isdigit() and 1 <= int(grade) <= 6 else student.grade
    student.department = department[:100] or student.department
    student.track = track_of(department) or student.track
    student.admission_year = student.admission_year or _year(row.get("admsnYear")) or _year(_text(row.get("stdno")))
    student.status = _short(row.get("schrsDtalSttnm"), 30) or student.status
    student.admission_type = _short(row.get("admsnSctinNm"), 30) or student.admission_type
    student.campus = _short(row.get("cmpsNm"), 30) or student.campus
    student.gpa = _number(row.get("gpa")) if row.get("gpa") not in (None, "") else student.gpa
    student.total_credits = _number(row.get("totGrCrdit")) if row.get("totGrCrdit") not in (None, "") else student.total_credits
    return student


def extract_diagnosis(payload: object, base: ImportedStudent | None = None) -> ImportedStudent:
    """졸업자가진단 기본값: 입학 연도, 교육과정 적용 연도, 이수 학기 수, 면제·교직·다전공 여부."""
    data = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(data, list):
        data = data[0] if data and isinstance(data[0], dict) else None
    if not isinstance(data, dict):
        raise ValueError("진단 기본값이 없습니다.")
    student = (base or ImportedStudent()).model_copy()
    student.admission_year = _year(data.get("admsnYear")) or student.admission_year
    student.curriculum_year = _year(data.get("crsdcApptnYear")) or student.curriculum_year
    semesters = _number(data.get("complSmstrCnt"))
    student.semesters = int(semesters) if semesters is not None and 0 <= semesters <= 20 else student.semesters
    student.math_exempt = _flag(data.get("mthmcScncExmptYn"))
    student.teaching = _flag(data.get("tcTrgprYn"))
    kind, dept = _short(data.get("cmbdcTpnm")), _short(data.get("cmbdcDprtnNm"), 60)
    student.other_major = f"{kind} {dept}".strip() if kind or dept else None
    return student


def ge_area(name: str) -> str | None:
    """교과구분 이름 → 시간표 조건의 교양 영역 (planner.GE_AREAS 와 맞춘다)."""
    compact = name.replace(" ", "")
    if "핵심인문" in compact:
        return "인문"
    if "핵심자연" in compact:
        return "자연"
    if "소양" in compact:
        return "첨성인소양"
    if "첨성인기초" in compact:
        return "첨성인기초"
    return None


def extract_requirements(payload: object) -> list[CreditStatus]:
    """교과구분별 기준 학점, 취득 학점, 충족 여부. 같은 이름이 두 번 나오면 첫 번째만 쓴다."""
    result: list[CreditStatus] = []
    seen: set[tuple[str, str]] = set()
    for row in _rows(payload):
        name = _text(row.get("univGrdtnAssssStnnm"))
        if not name:
            continue
        group = _text(row.get("sbjetSctin")) or None
        key = (name, group or "")
        if key in seen:
            continue
        seen.add(key)
        required, earned = _number(row.get("sndrdCrdit")), _number(row.get("complCrdit"))
        confirmed = _number(row.get("stgrCrdit2"))
        taking = sum(x for x in (_number(row.get("trmssStcuCrdit")), _number(row.get("ssnssStcuCrdit"))) if x)
        satisfied = _text(row.get("sffcnYn")).upper()
        is_ge = group == "교양" or ge_area(name) is not None
        result.append(
            CreditStatus(
                name=name[:60],
                group=group[:30] if group else None,
                major=_text(row.get("mltmjTpnm"))[:30] or None,
                required=required,
                earned=earned,
                confirmed=confirmed,
                in_progress=taking or None,
                satisfied=True if satisfied == "Y" else False if satisfied == "N" else None,
                shortage=max(0.0, required - earned) if required is not None and earned is not None else None,
                area=ge_area(name) if is_ge else None,
            )
        )
    return result[:80]


def extract_required_courses(payload: object) -> list[EssentialCourse]:
    """필수과목 이수정보. 이수 연도가 없으면 미이수, 연도는 있는데 성적이 없으면 수강 중. 성적 값은 남기지 않는다."""
    result: list[EssentialCourse] = []
    for row in _rows(payload):
        code, name = _text(row.get("sbjetCd")), _text(row.get("sbjetNm"))
        if not code and not name:
            continue
        year, grade = _text(row.get("complYear")), _text(row.get("gradsGradCd")).upper()
        state = "missing" if not year else "taking" if not grade else "failed" if grade in {"F", "NP"} else "done"
        result.append(
            EssentialCourse(
                code=code[:20] or None,
                name=(name or code)[:100],
                credits=_number(row.get("crdit")),
                state=state,
                major=_short(row.get("mltmjTpnm"), 30),
            )
        )
    return result[:100]


def extract_certifications(payload: object) -> list[Certification]:
    """졸업자격인정정보 (외국어·인증 등). 영역 이름과 합격·면제 여부만."""
    result: list[Certification] = []
    for row in _rows(payload):
        area = _text(row.get("grdtnRcgnnRelmSctnm"))
        if not area:
            continue
        result.append(Certification(area=area[:60], passed=_flag(row.get("pssxmYn")), exempt=_flag(row.get("exmptYn"))))
    return result[:30]


def shortage_areas(requirements: list[CreditStatus]) -> list[str]:
    """아직 못 채운 교양 영역 (부족 학점이 큰 순서)."""
    short = [r for r in requirements if r.area and (r.satisfied is False or (r.shortage or 0) > 0)]
    short.sort(key=lambda r: -(r.shortage or 0))
    areas: list[str] = []
    for item in short:
        if item.area not in areas:
            areas.append(item.area)
    return areas
