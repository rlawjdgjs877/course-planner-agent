"""조건에 맞고 시간이 겹치지 않는 시간표를 만든다.

AI 를 쓰지 않는 순수한 계산이다. 여기서 나온 시간표는 항상 규칙을 지킨다.
- 같은 과목(교과목코드)은 한 분반만 들어간다.
- 시간이 겹치지 않는다.
- 학점 합이 [min_credits, max_credits] 안에 있다.
- must_include, blocked_times, required_credits 를 모두 만족한다.
"""

import random
from collections import defaultdict

from app.schemas import Course, Meeting, Timetable, TimetableRequest, TimetableResult, TimeBlock
from app.services.course_time import DAYS, courses_conflict, meetings_overlap

WEEKDAYS = "월화수목금"
EXACT_NODES = 5_000  # 이 한도 안에 끝나면 모든 경우를 다 따져 본 것이다
RESTARTS = 40  # 한도를 넘으면 과목 순서를 바꿔 가며 여러 번 짧게 탐색한다
RESTART_NODES = 300
SLOT_MINUTES = 5
SLOTS_PER_DAY = 24 * 60 // SLOT_MINUTES


def _minutes(hhmm: str) -> int:
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def _is_blocked(course: Course, blocks: list[TimeBlock]) -> bool:
    for block in blocks:
        for day in block.day or DAYS:
            window = Meeting(day=day, start=block.start, end=block.end)
            if any(meetings_overlap(meeting, window) for meeting in course.meetings):
                return True
    return False


def _is_full(course: Course) -> bool:
    return (
        course.capacity is not None
        and course.enrolled is not None
        and course.enrolled >= course.capacity
    )


def _resolve_codes(names: list[str], courses: list[Course]) -> tuple[set[str], list[str]]:
    """교과목코드 또는 교과목명 목록을 교과목코드 집합으로 바꾼다. 못 찾은 것은 따로 돌려준다."""
    codes = {course.course_code for course in courses}
    by_name: dict[str, set[str]] = defaultdict(set)
    for course in courses:
        by_name[course.name].add(course.course_code)

    resolved: set[str] = set()
    unknown: list[str] = []
    for name in names:
        if name in codes:
            resolved.add(name)
        elif name in by_name:
            resolved |= by_name[name]
        else:
            unknown.append(name)
    return resolved, unknown


def _time_mask(course: Course) -> int:
    """수업 시간을 5분 단위 비트로 표시한다. 두 과목의 비트가 겹치면 시간이 겹친다."""
    mask = 0
    for meeting in course.meetings:
        first = _minutes(meeting.start) // SLOT_MINUTES
        last = -(-_minutes(meeting.end) // SLOT_MINUTES)
        offset = DAYS.index(meeting.day) * SLOTS_PER_DAY
        mask |= ((1 << (last - first)) - 1) << (offset + first)
    return mask


def summarize(
    courses: list[Course],
    preferred_free_days: list[str] | None = None,
    prefer_courses: list[str] | None = None,
) -> Timetable:
    """과목 목록의 학점 합, 공강 요일, 빈 시간, 점수를 계산한다.

    점수는 공강 희망 요일 > 유지하고 싶은 강좌 > 공강 요일 수 > 학점 > 수업 사이 빈 시간
    순으로 반영한다.
    """
    credits_by_category: dict[str, float] = defaultdict(float)
    by_day: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for course in courses:
        credits_by_category[course.category] += course.credits
        for meeting in course.meetings:
            by_day[meeting.day].append((_minutes(meeting.start), _minutes(meeting.end)))

    gap_minutes = 0
    for slots in by_day.values():
        slots.sort()
        gap_minutes += sum(
            max(0, later[0] - earlier[1]) for earlier, later in zip(slots, slots[1:])
        )

    total_credits = sum(course.credits for course in courses)
    free_days = [day for day in WEEKDAYS if day not in by_day]
    preferred_met = sum(1 for day in preferred_free_days or [] if day not in by_day)
    kept = sum(1 for course in courses if course.course_id in (prefer_courses or []))
    score = 10 * preferred_met + 4 * kept + 2 * len(free_days) + total_credits - gap_minutes / 60

    return Timetable(
        courses=sorted(courses, key=lambda course: course.course_id),
        total_credits=total_credits,
        credits_by_category=dict(credits_by_category),
        free_days=free_days,
        gap_minutes=gap_minutes,
        score=round(score, 2),
    )


def validate_timetable(courses: list[Course]) -> list[str]:
    """시간표의 문제점을 글로 돌려준다. 빈 목록이면 문제가 없다."""
    problems: list[str] = []
    seen: dict[str, Course] = {}
    for course in courses:
        if course.course_code in seen:
            problems.append(
                f"같은 과목이 두 번 들어 있습니다: {seen[course.course_code].course_id}, {course.course_id}"
            )
        seen[course.course_code] = course
    for index, first in enumerate(courses):
        for second in courses[index + 1 :]:
            if courses_conflict(first, second):
                problems.append(
                    f"시간이 겹칩니다: {first.name}({first.course_id}) / {second.name}({second.course_id})"
                )
    return problems


def generate_timetables(courses: list[Course], request: TimetableRequest) -> TimetableResult:
    must_codes, unknown = _resolve_codes(request.must_include, courses)
    if unknown:
        return TimetableResult(
            timetables=[],
            message=f"꼭 넣을 과목을 개설 강좌에서 찾지 못했습니다: {', '.join(unknown)}",
        )
    skip_codes = (
        _resolve_codes(request.exclude, courses)[0]
        | _resolve_codes(request.completed, courses)[0]
    )

    # 1. 들을 수 있는 분반만 남긴다.
    pool: list[Course] = [
        course
        for course in courses
        if course.course_code not in skip_codes
        and not _is_blocked(course, request.blocked_times)
        and not (request.exclude_full and _is_full(course))
    ]
    by_code: dict[str, list[int]] = defaultdict(list)
    for index, course in enumerate(pool):
        by_code[course.course_code].append(index)

    unavailable = sorted(must_codes - by_code.keys())
    if unavailable:
        return TimetableResult(
            timetables=[],
            message=(
                f"꼭 넣을 과목 중 조건에 맞는 분반이 없습니다: {', '.join(unavailable)}. "
                "이미 이수했거나, 제외 목록에 있거나, 금지 시간대와 겹치거나, 정원이 찼습니다."
            ),
        )

    # 2. 탐색을 빠르게 하려고 분반마다 필요한 값을 미리 계산해 둔다.
    masks = [_time_mask(course) for course in pool]
    credits_of = [course.credits for course in pool]
    category_of = [course.category for course in pool]
    code_of = [course.course_code for course in pool]
    on_preferred_day = [
        any(meeting.day in request.preferred_free_days for meeting in course.meetings)
        for course in pool
    ]
    needed = {category: need for category, need in request.required_credits.items() if need > 0}
    must = [by_code[code] for code in sorted(must_codes)]
    optional_codes = sorted(code for code in by_code if code not in must_codes)

    found: dict[frozenset[int], float] = {}
    state = {"nodes": 0, "limit": 0}

    def search(
        level: int,
        order: list[int],
        start: int,
        chosen: list[int],
        used: int,
        credits: float,
        by_category: dict[str, float],
    ) -> None:
        if state["nodes"] >= state["limit"]:
            return
        state["nodes"] += 1
        room = request.max_credits - credits
        deficit = sum(
            max(0.0, need - by_category.get(category, 0.0)) for category, need in needed.items()
        )
        if deficit > room:
            return  # 남은 학점으로는 교과구분별 조건을 채울 수 없다

        def pick(index: int, next_level: int, next_start: int) -> None:
            category = category_of[index]
            chosen.append(index)
            by_category[category] = by_category.get(category, 0.0) + credits_of[index]
            search(
                next_level,
                order,
                next_start,
                chosen,
                used | masks[index],
                credits + credits_of[index],
                by_category,
            )
            by_category[category] -= credits_of[index]
            chosen.pop()

        if level < len(must):  # 꼭 넣을 과목은 건너뛸 수 없다
            for index in must[level]:
                if credits_of[index] <= room and not masks[index] & used:
                    pick(index, level + 1, start)
            return

        if credits >= request.min_credits and deficit == 0:
            key = frozenset(chosen)
            if key not in found:
                found[key] = summarize(
                    [pool[index] for index in chosen],
                    request.preferred_free_days,
                    request.prefer_courses,
                ).score

        chosen_codes = {code_of[index] for index in chosen}
        for position in range(start, len(order)):
            index = order[position]
            if (
                credits_of[index] <= room
                and not masks[index] & used
                and code_of[index] not in chosen_codes
            ):
                pick(index, level, position + 1)

    def run(code_order: list[str], limit: int) -> bool:
        """정해진 과목 순서로 탐색한다. 한도 안에 끝냈으면 True."""
        state["nodes"], state["limit"] = 0, limit
        order = [index for code in code_order for index in by_code[code]]
        search(0, order, 0, [], 0, 0.0, {})
        return state["nodes"] < limit

    # 3. 과목이 적으면 모든 경우를 따져 보고, 많으면 순서를 바꿔 가며 여러 번 탐색한다.
    exhaustive = run(optional_codes, EXACT_NODES)
    if not exhaustive:
        rng = random.Random(0)  # 같은 요청에는 같은 결과가 나오도록 고정
        for _ in range(RESTARTS):
            keys = {code: rng.random() for code in optional_codes}
            # 공강 희망 요일에 수업이 없는 과목을 먼저 시도한다.
            code_order = sorted(
                optional_codes,
                key=lambda code: (all(on_preferred_day[i] for i in by_code[code]), keys[code]),
            )
            run(code_order, RESTART_NODES)

    # 4. 점수가 높은 순으로 고르되, 분반만 다르거나 한 과목만 다른 비슷한 시간표는 뒤로 미룬다.
    ranked = sorted(found, key=lambda key: (-found[key], sorted(key)))
    codes_in = {key: frozenset(code_of[index] for index in key) for key in ranked}
    selected: list[frozenset[int]] = []
    for key in ranked:
        if len(selected) == request.max_results:
            break
        if all(len(codes_in[key] ^ codes_in[other]) > 2 for other in selected):
            selected.append(key)
    for key in ranked:
        if len(selected) == request.max_results:
            break
        if key not in selected:
            selected.append(key)

    timetables = sorted(
        (
            summarize(
                [pool[index] for index in key],
                request.preferred_free_days,
                request.prefer_courses,
            )
            for key in selected
        ),
        key=lambda timetable: timetable.score,
        reverse=True,
    )

    message = None
    if not timetables:
        max_possible = sum(max(credits_of[i] for i in indexes) for indexes in by_code.values())
        if max_possible < request.min_credits:
            message = (
                f"조건에 맞는 과목을 모두 넣어도 {max_possible:g}학점이라 "
                f"최소 {request.min_credits:g}학점을 채울 수 없습니다. "
                "최소 학점을 낮추거나 금지 시간대를 줄여 보세요."
            )
        else:
            message = (
                "조건을 모두 만족하는 시간표를 찾지 못했습니다. 꼭 넣을 과목끼리 시간이 겹치거나, "
                "교과구분별 학점 조건이 학점 범위와 맞지 않을 수 있습니다. 조건을 하나씩 완화해 보세요."
            )
    return TimetableResult(timetables=timetables, message=message, truncated=not exhaustive)
