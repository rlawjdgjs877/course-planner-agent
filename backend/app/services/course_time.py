"""강의시간 글자를 요일·시작·종료 시각으로 바꾸고, 시간 충돌을 검사한다.

두 가지 표기를 지원한다.
- 실제 시간: "월 09:00 ~ 10:30, 수 09:00 ~ 10:30"
- 교시 코드: "월 1A,1B,2A 수 1A,1B,2A"  (1A = 09:00~09:30, 1B = 09:30~10:00 ...)
"""

import re

from app.schemas import Course, Meeting

DAYS = "월화수목금토일"

_REAL_TIME = re.compile(
    rf"((?:[{DAYS}][\s,/·]*)+)(\d{{1,2}}:\d{{2}})\s*[~\-–]\s*(\d{{1,2}}:\d{{2}})"
)
_PERIOD_TOKEN = re.compile(rf"[{DAYS}]|\d{{1,2}}[ABab]")


def _to_minutes(hhmm: str) -> int:
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def _to_hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def period_to_minutes(code: str) -> tuple[int, int]:
    """교시 코드 하나를 (시작 분, 종료 분)으로 바꾼다. 예: "1A" -> (540, 570)"""
    code = code.upper()
    number, half = int(code[:-1]), code[-1]
    if number == 0 and half == "A":
        # 학교 화면의 교시표에 0A 만 07:30-08:45 로 적혀 있어 그대로 따른다.
        return 7 * 60 + 30, 8 * 60 + 45
    start = (8 + number) * 60 + (30 if half == "B" else 0)
    return start, start + 30


def _merge(slots: dict[str, list[tuple[int, int]]]) -> list[Meeting]:
    """같은 요일에서 이어지거나 겹치는 구간을 하나로 합친다."""
    meetings: list[Meeting] = []
    for day in DAYS:
        merged: list[list[int]] = []
        for start, end in sorted(slots.get(day, [])):
            if merged and start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        meetings += [
            Meeting(day=day, start=_to_hhmm(start), end=_to_hhmm(end))
            for start, end in merged
        ]
    return meetings


def parse_real_time(text: str | None) -> list[Meeting]:
    """ "월 09:00 ~ 10:30, 수 09:00 ~ 10:30" 형태를 해석한다."""
    slots: dict[str, list[tuple[int, int]]] = {}
    for days, start, end in _REAL_TIME.findall(text or ""):
        start_min, end_min = _to_minutes(start), _to_minutes(end)
        if end_min <= start_min:
            continue
        for day in days:
            if day in DAYS:
                slots.setdefault(day, []).append((start_min, end_min))
    return _merge(slots)


def parse_period_codes(text: str | None) -> list[Meeting]:
    """ "월 1A,1B,2A 수 1A,1B,2A" 형태를 해석한다."""
    slots: dict[str, list[tuple[int, int]]] = {}
    day: str | None = None
    for token in _PERIOD_TOKEN.findall(text or ""):
        if token in DAYS:
            day = token
        elif day is not None:
            slots.setdefault(day, []).append(period_to_minutes(token))
    return _merge(slots)


def parse_meetings(real_time: str | None, period_codes: str | None) -> list[Meeting]:
    """실제 시간 표기를 먼저 쓰고, 해석되지 않으면 교시 코드를 쓴다."""
    return parse_real_time(real_time) or parse_period_codes(period_codes)


def meetings_overlap(a: Meeting, b: Meeting) -> bool:
    """두 수업이 같은 요일에 시간이 겹치는지. 끝나는 시각과 시작 시각이 같으면 겹치지 않는다."""
    return (
        a.day == b.day
        and _to_minutes(a.start) < _to_minutes(b.end)
        and _to_minutes(b.start) < _to_minutes(a.end)
    )


def courses_conflict(a: Course, b: Course) -> bool:
    """두 강좌를 같은 시간표에 넣을 수 없는지 (시간이 한 번이라도 겹치는지)."""
    return any(meetings_overlap(x, y) for x in a.meetings for y in b.meetings)
