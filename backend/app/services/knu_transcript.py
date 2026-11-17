"""학교 '이수성적 조회' 응답에서 이수 과목 목록을 뽑는다.

성적 값은 F, NP 를 걸러 내는 데만 쓰고 결과에는 남기지 않는다.
재이수, 이수 취소 같은 F/NP 외의 경우는 실제 응답으로 검증하지 않았다.
"""

from app.schemas import ImportedCourse

RESPONSE_MARKER = "searchTotalGradsInqrList"  # 학교 조회 요청 주소에 들어 있는 글자
EXCLUDED_GRADES = {"F", "NP"}


def _text(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _credits(value: object) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def extract_courses(payload: object) -> tuple[list[ImportedCourse], list[str]]:
    """응답의 data 배열을 과목 목록으로 바꾼다.

    같은 과목코드가 여러 번 나오면 첫 번째만 남기고, 그 코드를 따로 돌려준다
    (재이수일 수 있어 화면에서 확인을 부탁한다). 형식이 다르면 ValueError.
    """
    rows = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("응답에 data 배열이 없습니다.")

    courses: list[ImportedCourse] = []
    seen: set[str] = set()
    duplicates: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        if _text(row.get("gradsGradCd")).upper() in EXCLUDED_GRADES:
            continue
        code, name = _text(row.get("sbjetCd")), _text(row.get("sbjetNm"))
        if not code or not name:
            continue
        if code in seen:
            duplicates.add(code)
            continue
        seen.add(code)
        courses.append(
            ImportedCourse(
                code=code,
                name=name,
                credits=_credits(row.get("crdit")),
                category=_text(row.get("sbjetSctnm")) or None,
            )
        )
    return courses, sorted(duplicates)
