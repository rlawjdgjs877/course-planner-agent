"""에이전트 도구 정의 v3.2 의 generate_timetable.

프론트엔드가 보내는 조건(반드시 / 가능하면)을 시간표 생성기(services/timetable.py)의 조건으로
바꾸고, 결과를 v3.2 형식(status, 후보 tt_001…, 빠진 필수 과목과 이유, 대안)으로 돌려준다.

- 반드시: free_days, blocked_times, must_include, exclude, 최대 학점(학칙 상한 19), credits_strict 면 최소 학점
- 가능하면: avoid_times, target_credits, ge_areas, prefer_professor, base_candidate_id 의 과목 유지
- 상주캠퍼스 강좌, 교직 과목, 시간 미정 강좌, 토·일 수업(allow_weekend 가 아니면), 외국인 대상 교양,
  다른 단과대 학생용 기초 교양은 자동 추천에서 뺀다 (학생이 must_include 로 넣으면 넣는다).
- 선수과목(services/prerequisites.py, 권장 이수 순서): 이수 과목을 알려 주면 앞 단계를 듣지 않은 과목은
  자동 추천에서 빼고, 모르면 감점만 한다. 학생이 직접 넣은 과목은 넣되 prereq_issues 와 경고로 알린다.
- 만든 후보는 서버 메모리에 잠시 보관한다. 서버를 다시 켜면 사라진다.
"""

import re
import threading
from collections import OrderedDict

from app.schemas import (
    Alternative,
    Candidate,
    Course,
    GenerateTimetableRequest,
    GenerateTimetableResponse,
    OmittedCourse,
    PrereqIssue,
    TimeBlock,
    Timetable,
    TimetableRequest,
    TimetableResult,
)
from app.services import prerequisites
from app.services.timetable import _block_mask, _time_mask, generate_timetables

CREDIT_CAP = 19  # 도구 정의서의 기본 상한. 학칙으로 검증한 개인별 상한은 아니다.
TRACKS = {"advanced": "심컴", "ai": "인컴", "research": "첨컴", "platform": "플솦", "global": "글솦"}
# 프론트엔드나 채팅에서 다른 이름으로 올 수 있는 트랙 (소문자·공백 제거 후 비교)
TRACK_ALIASES = {
    "deep": "advanced", "심컴": "advanced", "심화컴퓨팅": "advanced", "심화컴퓨팅전공": "advanced",
    "aicomputing": "ai", "artificialintelligence": "ai", "인컴": "ai", "인공지능컴퓨팅": "ai", "인공지능컴퓨팅전공": "ai",
    "advancedresearch": "research", "첨컴": "research", "첨단컴퓨팅연구": "research", "첨단컴퓨팅연구전공": "research",
    "platformsw": "platform", "datascience": "platform", "플솦": "platform",
    "플랫폼sw·데이터과학전공": "platform", "플랫폼sw데이터과학전공": "platform", "플랫폼sw·데이터과학": "platform",
    "globalsw": "global", "글솦": "global", "글로벌sw융합": "global", "글로벌sw융합전공": "global",
}
GE_AREAS = {  # 교양 자료 이름 → 영역 이름 (frontend/app/lib/data/sources.json 과 같다)
    "foundation": "첨성인기초",
    "core-humanities": "첨성인핵심 · 인문",
    "core-natural": "첨성인핵심 · 자연",
    "literacy": "첨성인소양",
}
WEEKEND = ("토", "일")
PRIORITY_BONUS = 8.0  # 졸업자가진단의 미이수 필수과목
# 외국인 유학생 대상 교양: 국제처 개설 교양과 한국어 과목
FOREIGN_GE = re.compile(r"Korean Language|Practical Korean|Academic Korean|외국인을\s*위한|한국어로\s*보는")
# 다른 단과대 학생용 기초 교양 (인문사회계열·자연과학대학 전용)
OTHER_COLLEGE_GE = re.compile(r"^인문사회\s|^자연과학\s*코딩기초")
# 이공계 기초 교양 중 컴학 자료에 없는 것. 들을 수는 있으니 크게 감점만 한다.
SCIENCE_BASICS = re.compile(r"^(화학|물리학|생물학|일반생명과학|기초수학|물리학입문|생명과학입문)")
MAX_RELAXATIONS = 6  # 대안을 찾을 때 하나씩 풀어 보는 조건 수


class _CandidateStore:
    """만든 후보를 잠시 보관한다. 채팅으로 '1안에서 하나만 바꿔줘'를 할 때 쓴다."""

    def __init__(self, limit: int = 1000) -> None:
        self._items: OrderedDict[str, Candidate] = OrderedDict()
        self._counters = {"tt": 0, "tt_alt": 0}
        self._lock = threading.Lock()
        self._limit = limit

    def new_id(self, kind: str) -> str:
        with self._lock:
            self._counters[kind] += 1
            return f"{kind}_{self._counters[kind]:03d}"

    def save(self, candidate: Candidate) -> None:
        with self._lock:
            self._items[candidate.id] = candidate
            while len(self._items) > self._limit:
                self._items.popitem(last=False)

    def get(self, candidate_id: str | None) -> Candidate | None:
        with self._lock:
            return self._items.get(candidate_id or "")


store = _CandidateStore()


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", text)


def resolve_track(track: str | None) -> str | None:
    """트랙 id 나 별칭(deep, 심컴, 심화컴퓨팅전공 등)을 TRACKS 의 키로. 모르면 None."""
    if not track:
        return None
    key = _normalize(track).lower()
    if key in TRACKS:
        return key
    return TRACK_ALIASES.get(key)


def _computing_listed(course: Course) -> bool:
    return any(x.source == "computing" or x.source in TRACKS for x in course.listings)


def for_track(course: Course, track: str | None) -> Course:
    """같은 분반이 트랙마다 다른 이수구분으로 올라 있으면 학생 트랙 기준으로 고른다."""
    listings = course.listings
    chosen = next((x for x in listings if x.source == track), None) if track else None
    chosen = chosen or next((x for x in listings if x.source == "computing"), None) or (listings[0] if listings else None)
    area = next((GE_AREAS[x.source] for x in listings if x.source in GE_AREAS), None)
    update: dict = {"area": area}
    if chosen is not None:
        update.update(category=chosen.category, grade=chosen.grade, department=chosen.department or course.department)
    return course.model_copy(update=update)


def fit_bonus(course: Course, track: str | None, grade: int | None) -> float:
    """졸업 요건 자료가 들어오기 전까지 쓰는 임시 기준.

    학생 트랙(또는 컴학 공통)의 전공 과목을 우선하고, 학년을 알면 그 학년 과목을 우선하며
    두 학년 이상 위의 과목은 덜 고른다. 미이수 전공필수 같은 정확한 기준은 calc_credits 가 맡는다.
    """
    bonus = 0.0
    sources = {x.source for x in course.listings}
    if course.category != "교양" and (sources & ({track} if track else set()) or "computing" in sources):
        bonus += 2 + (course.credits or 0) * 0.5  # 전공 먼저 (3학점 전공 = +3.5)
        if "필수" in (course.category or ""):
            bonus += 2.5  # 전공필수는 부족한 교양(+3)보다 먼저
    if grade and course.grade and course.grade.isdigit():
        level = int(course.grade)
        if level == grade:
            bonus += 1
        elif level >= grade + 2:
            bonus -= 2
        elif course.category == "교양" and level < grade:
            bonus -= 0.5  # 아래 학년 대상 교양은 조금 덜 고른다
    if course.category == "교양" and not _computing_listed(course) and SCIENCE_BASICS.match(course.name):
        bonus -= 6
    return bonus


def not_recommended(course: Course, allow_weekend: bool = True) -> str | None:
    if "상주" in (course.building or ""):
        return "상주캠퍼스 강좌"
    if course.category == "교직":
        return "교직 과목"
    if not course.meetings:
        return "수업 시간 미정"
    if not allow_weekend and any(m.day in WEEKEND for m in course.meetings):
        return "토·일 수업"
    if not _computing_listed(course):
        if course.department == "국제처" or FOREIGN_GE.search(course.name):
            return "외국인 대상 교양"
        if OTHER_COLLEGE_GE.search(course.name):
            return "다른 단과대 학생용 교양"
    return None


def _matches(item: str, courses: list[Course]) -> list[Course]:
    """과목코드, 강좌번호(분반), 과목명 중 하나로 찾는다."""
    item = item.strip()
    by_section = [c for c in courses if c.course_id == item]
    if by_section:
        return by_section
    by_code = [c for c in courses if c.course_code == item]
    if by_code:
        return by_code
    name = _normalize(item)
    return [c for c in courses if _normalize(c.name) == name]


def _blocked(course: Course, blocks: list[TimeBlock]) -> bool:
    return bool(blocks) and bool(_time_mask(course) & _block_mask(blocks))


def _describe(block: TimeBlock) -> str:
    whole = block.start == "00:00" and block.end in ("24:00", "23:59")
    return f"{block.day}요일 공강" if whole else f"{block.day}요일 {block.start}~{block.end}"


class _Plan:
    """요청 하나를 처리한다."""

    def __init__(self, request: GenerateTimetableRequest, catalog: list[Course]) -> None:
        self.request = request
        self.warnings: list[str] = []
        self.max_credits = min(request.max_credits, CREDIT_CAP)
        if request.max_credits > CREDIT_CAP:
            self.warnings.append(f"수강 신청 상한 {CREDIT_CAP}학점에 맞춰 최대 {CREDIT_CAP}학점으로 찾았습니다.")
        self.min_credits = min(request.min_credits, self.max_credits)
        self.target = min(request.target_credits, self.max_credits)
        self.track = resolve_track(request.track)
        if request.track and not self.track:
            self.warnings.append(f"알 수 없는 트랙({request.track})이라 컴학 공통 기준으로 이수구분을 정했습니다.")
        self.courses = [for_track(course, self.track) for course in catalog]
        self.fit = {
            course.course_id: bonus
            for course in self.courses
            if (bonus := fit_bonus(course, self.track, request.grade))
        }
        # 졸업자가진단에서 아직 안 들은 필수과목은 가장 먼저 넣어 본다 (열린 분반이 있을 때).
        priority = {name.replace(" ", "") for name in request.priority_courses}
        for course in self.courses:
            if course.course_code in priority or course.name.replace(" ", "") in priority:
                self.fit[course.course_id] = self.fit.get(course.course_id, 0.0) + PRIORITY_BONUS

        base = store.get(request.base_candidate_id)
        if request.base_candidate_id and base is None:
            self.warnings.append(
                f"후보 {request.base_candidate_id}를 찾지 못해 처음부터 만들었습니다. 서버를 다시 켜면 후보가 지워집니다."
            )
        self.keep = [section.course_id for section in base.sections] if base else []
        self.base_id = request.base_candidate_id if base else None

        # 선수과목: 이수 과목을 알면 앞 단계 미이수 과목을 자동 추천에서 빼고, 모르면 감점만 한다.
        self.prereq = prerequisites.Checker(request.completed, self.courses, self.track)
        self.prereq_known = bool(request.completed)
        self.prereq_skipped: set[str] = set()
        self.prereq_flagged = {
            course.course_code for course in self.courses if self.prereq.issue(course.name) is not None
        }
        if not self.prereq_known:
            for course in self.courses:
                if course.course_code in self.prereq_flagged:
                    self.fit[course.course_id] = self.fit.get(course.course_id, 0.0) - 3

        self.completed = {c.course_code for item in request.completed for c in _matches(item, self.courses)} | {
            item.strip() for item in request.completed
        }
        self.excluded_codes: set[str] = set()
        self.excluded_sections: set[str] = set()
        for item in request.exclude:
            found = _matches(item, self.courses)
            if found and found[0].course_id == item.strip():
                self.excluded_sections |= {c.course_id for c in found}
            else:
                self.excluded_codes |= {c.course_code for c in found}

        self.free_blocks = [TimeBlock(day=day, start="00:00", end="24:00") for day in request.free_days]
        self.blocked = [TimeBlock(day=b.day, start=b.start, end=b.end) for b in request.blocked_times]
        self.avoid = [TimeBlock(day=b.day, start=b.start, end=b.end) for b in request.avoid_times]

    # ---------- 반드시 넣을 과목 ----------

    def check_musts(self, free: list[TimeBlock], blocked: list[TimeBlock]):
        """(넣을 수 있는 과목코드, 분반 제한, 빠진 과목) — 시간 조건은 주어진 것으로 본다."""
        ok: list[str] = []
        only: dict[str, set[str]] = {}
        omitted: list[OmittedCourse] = []
        for item in self.request.must_include:
            found = _matches(item, self.courses)
            if not found:
                omitted.append(OmittedCourse(item=item, reason="not_offered", detail="이번 학기 개설 강좌에서 찾지 못했습니다."))
                continue
            code, name = found[0].course_code, found[0].name
            if code in ok:
                continue
            gone = lambda reason, detail: omitted.append(OmittedCourse(item=item, code=code, name=name, reason=reason, detail=detail))
            sections = [c for c in found if c.course_id not in self.excluded_sections]
            if code in self.completed:
                gone("already_completed", "이미 이수한 과목입니다.")
            elif code in self.excluded_codes or not sections:
                gone("excluded", "넣지 않을 과목에도 들어 있습니다.")
            elif not (free_ok := [c for c in sections if not _blocked(c, free)]):
                days = ", ".join(sorted({m.day for c in sections for m in c.meetings}))
                gone("free_day_conflict", f"모든 분반이 비워야 하는 요일에 있습니다 (수업 요일: {days}).")
            elif not (usable := [c for c in free_ok if not _blocked(c, blocked)]):
                gone("blocked_time", "모든 분반이 비워야 하는 시간과 겹칩니다.")
            else:
                ok.append(code)
                if found[0].course_id == item.strip():
                    only[code] = {c.course_id for c in usable}
        return ok, only, omitted

    def pool(self, musts: list[str], only: dict[str, set[str]]) -> list[Course]:
        result = []
        for course in self.courses:
            if course.course_id in self.excluded_sections:
                continue
            if course.course_code in only and course.course_id not in only[course.course_code]:
                continue
            if course.course_code not in musts and not_recommended(course, self.request.allow_weekend):
                continue
            if (
                self.prereq_known
                and course.course_code in self.prereq_flagged
                and course.course_code not in musts
                and course.course_id not in self.keep
            ):
                self.prereq_skipped.add(course.course_code)
                continue
            result.append(course)
        return result

    def run(self, pool, musts, min_credits, blocks, limit) -> TimetableResult:
        return generate_timetables(
            pool,
            TimetableRequest(
                min_credits=min_credits,
                max_credits=self.max_credits,
                must_include=musts,
                exclude=sorted(self.excluded_codes),
                completed=sorted(self.completed),
                blocked_times=blocks,
                prefer_courses=self.keep,
                avoid_times=self.avoid,
                target_credits=self.target,
                prefer_professors=self.request.prefer_professor,
                prefer_areas=self.request.ge_areas,
                section_bonus=self.fit,
                max_results=limit,
            ),
        )

    def solve(self, free: list[TimeBlock], blocked: list[TimeBlock], limit: int):
        """(결과, 넣은 필수 과목, 빠진 필수 과목, 최소 학점 미달 여부)"""
        musts, only, omitted = self.check_musts(free, blocked)
        blocks = free + blocked
        pool = self.pool(musts, only)
        result = self.run(pool, musts, self.min_credits, blocks, limit)
        if not result.timetables and musts:
            # 필수 과목끼리 시간이 겹치면, 앞에서부터 하나씩 넣어 보며 함께 넣을 수 없는 과목을 뺀다.
            kept: list[str] = []
            for code in musts:
                if self.run(pool, kept + [code], 0, blocks, 1).timetables:
                    kept.append(code)
                else:
                    name = next((c.name for c in self.courses if c.course_code == code), code)
                    item = next((i for i in self.request.must_include if _matches(i, self.courses) and _matches(i, self.courses)[0].course_code == code), code)
                    omitted.append(OmittedCourse(item=item, code=code, name=name, reason="time_conflict",
                                                 detail="다른 필수 과목과 모든 분반의 시간이 겹칩니다."))
            if len(kept) < len(musts):
                musts = kept
                result = self.run(pool, musts, self.min_credits, blocks, limit)
        below_min = False
        if not result.timetables and not self.request.credits_strict:
            result = self.run(pool, musts, 0, blocks, limit)
            below_min = bool(result.timetables)
        return result, musts, omitted, below_min

    # ---------- 결과 ----------

    def candidate(self, timetable: Timetable, kind: str) -> Candidate:
        warnings = []
        for course in timetable.courses:
            label = f"{course.name} {course.section or ''}분반".strip()
            if _blocked(course, self.avoid):
                warnings.append(f"{label}이 피하고 싶은 시간과 겹칩니다.")
            if not course.meetings:
                warnings.append(f"{label}은 수업 시간이 정해지지 않았습니다.")
        issues = prerequisites.issues_for(timetable.courses, [], [], checker=self.prereq)
        warnings += [prerequisites.describe(issue) for issue in issues]
        result = Candidate(
            id=store.new_id(kind),
            sections=timetable.courses,
            total_credits=timetable.total_credits,
            credits_by_category=timetable.credits_by_category,
            free_days=timetable.free_days,
            gap_minutes=timetable.gap_minutes,
            score=timetable.score,
            warnings=warnings,
            prereq_issues=[PrereqIssue(**issue) for issue in issues],
        )
        store.save(result)
        return result

    def alternatives(self, current_musts: list[str], current_credits: float) -> list[Alternative]:
        """반드시 조건을 하나씩 풀어 보고, 나아지는 안을 최대 2개 고른다."""
        trials: list[tuple[str, list[TimeBlock], list[TimeBlock]]] = []
        for block in self.free_blocks:
            trials.append((f"{block.day}요일 공강을 풀면", [b for b in self.free_blocks if b is not block], self.blocked))
        for block in self.blocked:
            trials.append((f"{_describe(block)} 수업을 허용하면", self.free_blocks, [b for b in self.blocked if b is not block]))
        found = []
        for label, free, blocked in trials[:MAX_RELAXATIONS]:
            result, musts, _, below = self.solve(free, blocked, 1)
            if not result.timetables:
                continue
            best = result.timetables[0]
            gained = [code for code in musts if code not in current_musts]
            if len(musts) > len(current_musts) or (len(musts) == len(current_musts) and best.total_credits > current_credits):
                found.append((len(musts), best.total_credits, label, best, gained))
        found.sort(key=lambda x: (-x[0], -x[1]))
        alternatives = []
        for _, credits, label, timetable, gained in found[:2]:
            names = [next(c.name for c in self.courses if c.course_code == code) for code in gained]
            description = f"{label} {credits:g}학점" + (f" ({', '.join(names)} 포함)" if names else "")
            alternatives.append(
                Alternative(
                    id="",
                    relaxed=[label.removesuffix("을 풀면").removesuffix(" 수업을 허용하면")],
                    description=description,
                    candidate=self.candidate(timetable, "tt_alt"),
                )
            )
        for alternative in alternatives:
            alternative.id = alternative.candidate.id
        return alternatives

    def missed_priority(self, candidates: list[Candidate]) -> list[str]:
        """졸업자가진단의 미이수 필수과목 중 1안에 못 넣은 과목과 그 이유."""
        if not self.request.priority_courses:
            return []
        placed = {section.course_code for section in candidates[0].sections} if candidates else set()
        missed: list[str] = []
        for item in dict.fromkeys(self.request.priority_courses):
            found = _matches(item, self.courses)
            code = found[0].course_code if found else item.strip()
            name = found[0].name if found else item.strip()
            if code in placed or code in self.completed or code in self.excluded_codes:
                continue
            if not found:
                reason = "이번 학기 미개설"
            elif code in self.prereq_skipped:
                reason = "앞 단계 과목을 먼저 들어야 함"
            elif all(not_recommended(course, self.request.allow_weekend) for course in found):
                reason = not_recommended(found[0], self.request.allow_weekend) or "추천 제외"
            else:
                reason = "다른 과목·조건과 시간이나 학점이 맞지 않음"
            missed.append(f"{name}({reason})")
        return missed

    def respond(self) -> GenerateTimetableResponse:
        result, musts, omitted, below_min = self.solve(self.free_blocks, self.blocked, self.request.max_candidates)
        candidates = [self.candidate(timetable, "tt") for timetable in result.timetables]
        warnings = list(self.warnings)
        if below_min and candidates:
            warnings.append(f"최소 {self.min_credits:g}학점을 채우는 시간표가 없어 {candidates[0].total_credits:g}학점으로 만들었습니다.")
        # 학생이 직접 넣은 과목의 선수과목 경고는 응답 전체 경고에도 한 줄씩 올린다.
        must_lines: dict[str, None] = {}
        for candidate in candidates:
            codes = {section.course_id: section.course_code for section in candidate.sections}
            for issue in candidate.prereq_issues:
                if codes.get(issue.course_id) in musts:
                    must_lines[prerequisites.describe(issue.model_dump())] = None
        warnings += list(must_lines)
        if self.prereq_skipped:
            warnings.append(
                f"선수과목(권장 이수 순서)의 앞 단계를 이수하지 않은 {len(self.prereq_skipped)}과목은 자동 추천에서 뺐습니다."
            )
        elif not self.prereq_known and any(c.prereq_issues for c in candidates):
            warnings.append("이수 과목 정보가 없어 선수과목은 확인용으로만 표시했습니다. 이수 과목을 알려 주면 더 정확합니다.")
        if missed := self.missed_priority(candidates):
            warnings.append("먼저 넣으려던 미이수 필수과목 중 빠진 과목: " + ", ".join(missed))
        if result.truncated:
            warnings.append("과목이 많아 일부 조합만 살펴봤습니다. 더 좋은 조합이 있을 수 있습니다.")
        if not candidates:
            status = "infeasible"
            if result.message:
                warnings.append(result.message)
        elif omitted or below_min:
            status = "partial"
        else:
            status = "success"
        alternatives = []
        if status != "success" and (self.free_blocks or self.blocked):
            alternatives = self.alternatives(musts, candidates[0].total_credits if candidates else 0)
        return GenerateTimetableResponse(
            status=status,
            optimal=False,
            candidates=candidates,
            applied={
                "min_credits": self.min_credits,
                "target_credits": self.target,
                "max_credits": self.max_credits,
                "credits_strict": self.request.credits_strict,
                "track": self.track,
                "grade": self.request.grade,
                "allow_weekend": self.request.allow_weekend,
                "base_candidate_id": self.base_id,
            },
            omitted_required=omitted,
            warnings=warnings,
            alternatives=alternatives,
        )


def generate(request: GenerateTimetableRequest, catalog: list[Course]) -> GenerateTimetableResponse:
    return _Plan(request, catalog).respond()
