"""조건에 맞고 시간이 겹치지 않는 시간표를 만든다.

AI 를 쓰지 않는 순수한 계산이다. 여기서 나온 시간표는 항상 규칙을 지킨다.
- 같은 과목(교과목코드)은 한 분반만 들어간다.
- 시간이 겹치지 않는다.
- 학점 합이 [min_credits, max_credits] 안에 있다.
- must_include, blocked_times, required_credits 를 모두 만족한다.
"""

import random
from collections import defaultdict

from app.schemas import Course, Timetable, TimetableRequest, TimetableResult, TimeBlock
from app.services.course_time import DAYS, courses_conflict

WEEKDAYS = "월화수목금"
EXACT_CODES = 40  # 과목이 이보다 적으면 모든 경우를 따져 본다
EXACT_NODES = 5_000  # 이 한도 안에 끝나면 모든 경우를 다 따져 본 것이다
RESTARTS = 80  # 과목이 많으면 일부만 뽑아, 뽑는 과목을 바꿔 가며 여러 번 짧게 탐색한다
RESTART_NODES = 300
SAMPLE_CODES = 60  # 한 번 탐색할 때 뽑는 과목 수
SAMPLE_PER_CATEGORY = 12
FAVORED_CODES = 25  # 매번 넣는 높은 점수 과목 수  # 그중 꼭 채워야 하는 영역마다 넣는 과목 수
SLOT_MINUTES = 5
SLOTS_PER_DAY = 24 * 60 // SLOT_MINUTES


def _minutes(hhmm: str) -> int:
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def _block_mask(blocks: list[TimeBlock]) -> int:
    """수업을 넣으면 안 되는 시간대를 _time_mask 와 같은 비트로 표시한다."""
    mask = 0
    for block in blocks:
        first = _minutes(block.start) // SLOT_MINUTES
        last = -(-_minutes(block.end) // SLOT_MINUTES)
        span = ((1 << max(0, last - first)) - 1) << first
        for day in block.day or DAYS:
            if day in DAYS:
                mask |= span << (DAYS.index(day) * SLOTS_PER_DAY)
    return mask


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


def course_bonus(course: Course, request: TimetableRequest | None, avoid_mask: int = 0) -> float:
    """과목 하나가 '가능하면' 조건을 얼마나 지키는지. 시간표 점수에 더한다."""
    if request is None:
        return 0.0
    bonus = request.section_bonus.get(course.course_id, 0.0)
    if course.course_id in request.prefer_courses:
        bonus += 4  # 지금 시간표에 있던 과목은 유지
    if course.professor and any(name and name in course.professor for name in request.prefer_professors):
        bonus += 2
    if course.area and any(area and area in course.area for area in request.prefer_areas):
        bonus += 3
    if avoid_mask and _time_mask(course) & avoid_mask:
        bonus -= 3  # 피하고 싶은 시간에 수업이 있다
    return bonus


def credits_score(credits: float, target: float | None) -> float:
    """목표 학점이 없으면 많을수록, 있으면 목표에 가까울수록 높다."""
    return credits if target is None else target - 2 * abs(credits - target)


def summarize(courses: list[Course], request: TimetableRequest | None = None) -> Timetable:
    """과목 목록의 학점 합, 공강 요일, 빈 시간, 점수를 계산한다.

    점수는 공강 희망 요일 > 유지하고 싶은 강좌, 선호 교수·영역, 피할 시간 > 공강 요일 수
    > 학점 > 수업 사이 빈 시간 순으로 반영한다.
    """
    preferred_free_days = request.preferred_free_days if request else []
    avoid_mask = _block_mask(request.avoid_times) if request else 0
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
    preferred_met = sum(1 for day in preferred_free_days if day not in by_day)
    bonus = sum(course_bonus(course, request, avoid_mask) for course in courses)
    target = request.target_credits if request else None
    score = 10 * preferred_met + bonus + 2 * len(free_days) + credits_score(total_credits, target) - gap_minutes / 60

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
    blocked = _block_mask(request.blocked_times)
    pool: list[Course] = []
    masks: list[int] = []
    for course in courses:
        if course.course_code in skip_codes or (request.exclude_full and _is_full(course)):
            continue
        mask = _time_mask(course)
        if mask & blocked:
            continue
        pool.append(course)
        masks.append(mask)
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
    credits_of = [course.credits for course in pool]
    category_of = [course.category for course in pool]
    code_of = [course.course_code for course in pool]
    on_preferred_day = [
        any(meeting.day in request.preferred_free_days for meeting in course.meetings)
        for course in pool
    ]
    slots_of = [
        [(DAYS.index(m.day), _minutes(m.start), _minutes(m.end)) for m in course.meetings]
        for course in pool
    ]
    kept_ids = set(request.prefer_courses)
    is_kept = [course.course_id in kept_ids for course in pool]
    avoid_mask = _block_mask(request.avoid_times)
    bonus_of = [course_bonus(course, request, avoid_mask) for course in pool]
    day_bits_of = [sum({1 << DAYS.index(m.day) for m in course.meetings}) for course in pool]
    weekday_bits = [1 << day for day in range(len(WEEKDAYS))]
    preferred_days = [DAYS.index(day) for day in request.preferred_free_days if day in DAYS]
    needed = {category: need for category, need in request.required_credits.items() if need > 0}
    must = [by_code[code] for code in sorted(must_codes)]
    optional_codes = sorted(code for code in by_code if code not in must_codes)

    preferred_bits = [1 << day for day in preferred_days]

    def rough_score(days: int, bonus: float, credits: float) -> float:
        """빈 시간을 뺀 점수. 탐색 중 조합마다 계산해야 해서 가볍게 만든다."""
        free = sum(1 for bit in weekday_bits if not days & bit)
        met = sum(1 for bit in preferred_bits if not days & bit)
        return 10 * met + bonus + 2 * free + credits_score(credits, request.target_credits)

    def quick_score(chosen: list[int]) -> float:
        """summarize 와 같은 점수 (빈 시간 포함)."""
        by_day: dict[int, list[tuple[int, int]]] = {}
        credits, bonus = 0.0, 0.0
        for index in chosen:
            credits += credits_of[index]
            bonus += bonus_of[index]
            for day, start, end in slots_of[index]:
                by_day.setdefault(day, []).append((start, end))
        gap = 0
        for slots in by_day.values():
            if len(slots) > 1:
                slots.sort()
                gap += sum(max(0, later[0] - earlier[1]) for earlier, later in zip(slots, slots[1:]))
        free = sum(1 for day in range(len(WEEKDAYS)) if day not in by_day)
        met = sum(1 for day in preferred_days if day not in by_day)
        return 10 * met + bonus + 2 * free + credits_score(credits, request.target_credits) - gap / 60

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
        days: int = 0,
        bonus: float = 0.0,
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
                days | day_bits_of[index],
                bonus + bonus_of[index],
            )
            by_category[category] -= credits_of[index]
            chosen.pop()

        if level < len(must):  # 꼭 넣을 과목은 건너뛸 수 없다
            for index in must[level]:
                if state["nodes"] >= state["limit"]:
                    return
                if credits_of[index] <= room and not masks[index] & used:
                    pick(index, level + 1, start)
            return

        if credits >= request.min_credits and deficit == 0:
            key = frozenset(chosen)
            if key not in found:
                found[key] = rough_score(days, bonus, credits)

        chosen_codes = {code_of[index] for index in chosen}
        for position in range(start, len(order)):
            if state["nodes"] >= state["limit"]:
                return  # 한도에 닿으면 남은 후보를 하나씩 확인하지 않고 바로 멈춘다
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

    # 3. 과목이 적으면 모든 경우를 따져 본다. 많으면 매번 일부 과목만 뽑아 짧게 탐색하고,
    #    뽑는 과목을 바꿔 가며 여러 번 되풀이한다. (전체를 매번 훑으면 과목 수천 개에서 수 초가 걸린다.)
    exhaustive = len(optional_codes) <= EXACT_CODES and run(optional_codes, EXACT_NODES)
    if not exhaustive:
        rng = random.Random(0)  # 같은 요청에는 같은 결과가 나오도록 고정
        # 지금 시간표의 과목은 항상 후보에 넣어, 수정 요청 뒤에도 시간표가 크게 바뀌지 않게 한다.
        always = [code for code in optional_codes if any(is_kept[i] for i in by_code[code])]
        # 점수가 높은 과목(학생 트랙의 전공 등)은 무작위로 빠지지 않게 매번 넣는다. 전공 먼저.
        favored = sorted(
            (code for code in optional_codes if max(bonus_of[i] for i in by_code[code]) >= 2.5),
            key=lambda code: -max(bonus_of[i] for i in by_code[code]),
        )[:FAVORED_CODES]
        always += [code for code in favored if code not in always]
        codes_by_category: dict[str, list[str]] = {category: [] for category in needed}
        for code in optional_codes:
            category = category_of[by_code[code][0]]
            if category in codes_by_category:
                codes_by_category[category].append(code)

        for _ in range(RESTARTS):
            picked = list(always)
            for codes in codes_by_category.values():  # 꼭 채워야 하는 영역의 과목
                picked += rng.sample(codes, min(SAMPLE_PER_CATEGORY, len(codes)))
            picked += rng.sample(optional_codes, min(SAMPLE_CODES, len(optional_codes)))
            keys = {code: rng.random() for code in dict.fromkeys(picked)}
            # 지금 시간표의 과목, 공강 희망 요일에 수업이 없는 과목 순으로 먼저 시도한다.
            code_order = sorted(
                keys,
                key=lambda code: (
                    not any(is_kept[i] for i in by_code[code]),
                    code not in favored,
                    all(on_preferred_day[i] for i in by_code[code]),
                    keys[code],
                ),
            )
            run(code_order, RESTART_NODES)

    # 4. 점수가 높은 순으로 고르되, 분반만 다르거나 한 과목만 다른 비슷한 시간표는 뒤로 미룬다.
    # 빠른 점수로 상위 몇십 개만 고른 뒤, 빈 시간까지 따진 점수로 다시 줄 세운다.
    shortlist = sorted(found, key=lambda key: (-found[key], sorted(key)))[: max(60, request.max_results * 20)]
    found = {key: quick_score(list(key)) for key in shortlist}
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
            summarize([pool[index] for index in key], request)
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
