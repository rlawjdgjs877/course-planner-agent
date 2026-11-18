"""과목 데이터 형식.

학교 '수업시간표 및 강의계획서 조회' 화면의 열 구성을 그대로 따른다.
backend/app/data/courses.json 은 Course 의 목록이다.
"""

from typing import Literal

from pydantic import BaseModel, Field, SecretStr, model_validator


class Meeting(BaseModel):
    """수업 한 번. 예: 월요일 09:00~10:30"""

    day: str = Field(description="요일 한 글자: 월 화 수 목 금 토 일")
    start: str = Field(description="시작 시각 HH:MM")
    end: str = Field(description="종료 시각 HH:MM")


class CourseListing(BaseModel):
    """같은 분반이 어느 자료(트랙, 교양 영역)에 어떤 이수구분과 학년으로 올라 있는지."""

    source: str = Field(description="자료 이름. 트랙 id(advanced, ai, research, platform, global), computing(컴학 공통), 교양 영역 등")
    category: str = Field(description="그 자료에서의 교과구분. 예: 전공필수, 공학전공, 교양")
    grade: str | None = Field(default=None, description="그 자료에서의 대상 학년. *는 전학년")
    department: str | None = Field(default=None, description="그 자료에서의 개설학과")


class Course(BaseModel):
    """개설 강좌 하나 (분반 단위)."""

    year: int = Field(description="개설연도")
    semester: str = Field(description="개설학기. 예: 1학기, 2학기")
    grade: str | None = Field(default=None, description="대상 학년")
    category: str = Field(description="교과구분. 예: 전공필수, 전공선택, 교양")
    college: str | None = Field(default=None, description="개설대학")
    department: str | None = Field(default=None, description="개설학과")

    course_id: str = Field(description="강좌번호 (교과목코드-분반). 예: ABCD0001-001")
    course_code: str = Field(description="교과목코드. 분반이 달라도 같은 과목이면 같다")
    section: str | None = Field(default=None, description="분반")
    name: str = Field(description="교과목명")

    credits: float = Field(description="학점")
    lecture_hours: float | None = Field(default=None, description="강의 시수")
    lab_hours: float | None = Field(default=None, description="실습 시수")

    professor: str | None = Field(default=None, description="담당교수")
    time_raw: str | None = Field(default=None, description="화면에 표시된 강의시간 원문")
    meetings: list[Meeting] = Field(
        default_factory=list,
        description="해석된 수업 시간. 비어 있으면 시간이 정해지지 않은 강좌(원격 등)",
    )

    building: str | None = Field(default=None, description="강의실 (건물)")
    room: str | None = Field(default=None, description="호실번호")
    capacity: int | None = Field(default=None, description="수강정원")
    enrolled: int | None = Field(default=None, description="수강신청 인원")
    listings: list[CourseListing] = Field(
        default_factory=list, description="트랙·영역별 이수구분. 같은 분반이 여러 자료에 다르게 올라 있을 수 있다"
    )
    area: str | None = Field(default=None, description="교양 영역. 시간표를 짤 때 listings 에서 정한다")


class CourseList(BaseModel):
    sample: bool = Field(description="가짜 샘플 데이터인지 (실제 courses.json 이 아직 없을 때 True)")
    courses: list[Course]


class ImportedCourse(BaseModel):
    """학생이 이미 이수한 과목. 학교 화면에서 불러오거나 직접 입력한다. 성적은 담지 않는다."""

    code: str = Field(description="과목코드")
    name: str = Field(description="과목명")
    credits: float | None = Field(default=None, description="학점")
    category: str | None = Field(default=None, description="이수구분")


class KnuImportStatus(BaseModel):
    enabled: bool = Field(description="서버 설정에서 이 실험 기능이 켜져 있는지")
    installed: bool = Field(description="Playwright 가 설치되어 있는지")
    available: bool = Field(description="지금 이 요청자가 쓸 수 있는지")
    reason: str | None = Field(default=None, description="쓸 수 없을 때 이유")
    idle_minutes: int = Field(description="이만큼 아무 요청이 없으면 연결을 닫는다")


class KnuStartRequest(BaseModel):
    consent: bool = Field(description="안내를 읽고 본인 계정으로만 쓴다는 동의")


class KnuStartResponse(BaseModel):
    session: str = Field(description="이 연결의 토큰. 이후 요청의 X-Import-Session 헤더에 넣는다")


class KnuInput(BaseModel):
    """원격 학교 화면에 보내는 입력 하나."""

    type: Literal["click", "key", "text", "scroll"]
    x: float | None = Field(default=None, ge=0, le=1280)
    y: float | None = Field(default=None, ge=0, le=800)
    key: str | None = Field(default=None, max_length=20)
    text: str | None = Field(default=None, max_length=200)
    delta: float | None = Field(default=None, ge=-2000, le=2000)


class KnuLogin(BaseModel):
    """학교 로그인 칸에 채울 값. 저장하거나 로그에 남기지 않는다."""

    user_id: str = Field(min_length=1, max_length=100)
    password: SecretStr = Field(min_length=1, max_length=200)


class KnuFrameRequest(BaseModel):
    have: str | None = Field(default=None, description="학생 화면에 이미 있는 화면의 frame_id")


class KnuFrame(BaseModel):
    image: str | None = Field(default=None, description="원격 화면 JPEG (base64). 바뀌지 않았으면 비어 있다")
    frame_id: str | None = Field(default=None, description="지금 화면의 식별자")
    status: str = Field(description="지금 무엇을 하고 있는지")
    finished: bool = Field(description="이수 과목을 읽었는지")
    login_form: bool = Field(default=False, description="학교 로그인 칸이 화면에 보이는지")
    courses: list[ImportedCourse] = Field(default_factory=list)
    duplicates: list[str] = Field(default_factory=list, description="여러 번 나온 과목코드")
    expires_in: int = Field(description="이 연결이 자동으로 닫히기까지 남은 초")


class KnuStopRequest(BaseModel):
    session: str | None = Field(default=None, description="헤더를 못 붙이는 경우(페이지를 닫을 때)용")


class RequiredCourse(BaseModel):
    course_code: str = Field(description="교과목코드")
    name: str = Field(description="교과목명")


class GraduationRequirement(BaseModel):
    """졸업 요건. 학과와 입학연도마다 하나."""

    department: str = Field(description="학과")
    admission_year: int = Field(description="입학연도")
    total_credits: float = Field(description="졸업에 필요한 총 학점")
    credits: dict[str, float] = Field(
        default_factory=dict, description="영역(교과구분)별 최소 학점. 예: {'전공필수': 30}"
    )
    required_courses: list[RequiredCourse] = Field(
        default_factory=list, description="꼭 들어야 하는 과목"
    )


class RequirementList(BaseModel):
    sample: bool = Field(description="가짜 샘플 데이터인지")
    requirements: list[GraduationRequirement]


class TimeBlock(BaseModel):
    """수업을 넣으면 안 되는 시간대. 예: 금요일 전체, 매일 09:00~10:00"""

    day: str | None = Field(default=None, description="요일 한 글자. 비우면 모든 요일")
    start: str = Field(default="00:00", description="시작 시각 HH:MM")
    end: str = Field(default="24:00", description="종료 시각 HH:MM")


class TimetableRequest(BaseModel):
    """시간표 생성 조건. 사용자의 말을 AI가 이 형식으로 바꿔서 넘긴다."""

    min_credits: float = Field(description="이번 학기 최소 학점")
    max_credits: float = Field(description="이번 학기 최대 학점")

    # 반드시 지켜야 하는 조건
    must_include: list[str] = Field(
        default_factory=list, description="꼭 넣을 과목 (교과목코드 또는 교과목명)"
    )
    exclude: list[str] = Field(
        default_factory=list, description="넣지 않을 과목 (교과목코드 또는 교과목명)"
    )
    completed: list[str] = Field(
        default_factory=list, description="이미 이수한 과목 (교과목코드 또는 교과목명)"
    )
    blocked_times: list[TimeBlock] = Field(
        default_factory=list, description="수업을 넣으면 안 되는 시간대"
    )
    required_credits: dict[str, float] = Field(
        default_factory=dict,
        description="교과구분별로 이번 학기에 채울 최소 학점. 예: {'전공필수': 6}",
    )
    exclude_full: bool = Field(default=False, description="정원이 찬 강좌를 제외할지")

    # 가능하면 반영하는 선호 (점수에만 영향)
    preferred_free_days: list[str] = Field(
        default_factory=list, description="공강이면 좋은 요일"
    )

    prefer_courses: list[str] = Field(
        default_factory=list,
        description="가능하면 유지할 강좌번호. 채팅으로 고칠 때 지금 시간표와 비슷한 결과를 내는 데 쓴다",
    )
    avoid_times: list[TimeBlock] = Field(
        default_factory=list, description="가능하면 피할 시간대 (겹치면 점수가 깎인다)"
    )
    target_credits: float | None = Field(
        default=None, description="목표 학점. 정하면 학점이 이 값에 가까울수록 점수가 높다"
    )
    prefer_professors: list[str] = Field(default_factory=list, description="가능하면 넣을 교수 이름")
    prefer_areas: list[str] = Field(
        default_factory=list, description="가능하면 넣을 교양 영역 (Course.area 에 이 글자가 들어 있으면)"
    )
    section_bonus: dict[str, float] = Field(
        default_factory=dict, description="강좌번호별로 점수에 더할 값. 학생에게 맞는 과목을 우선할 때 쓴다"
    )

    max_results: int = Field(default=5, ge=1, le=20, description="돌려줄 시간표 개수")

    @model_validator(mode="after")
    def _check_credit_range(self) -> "TimetableRequest":
        if self.min_credits > self.max_credits:
            raise ValueError("min_credits 는 max_credits 보다 클 수 없습니다")
        return self


class Timetable(BaseModel):
    """만들어진 시간표 하나."""

    courses: list[Course]
    total_credits: float
    credits_by_category: dict[str, float] = Field(description="교과구분별 학점 합")
    free_days: list[str] = Field(description="월~금 중 수업이 없는 요일")
    gap_minutes: int = Field(description="수업 사이 빈 시간의 합 (분)")
    score: float = Field(description="높을수록 선호에 잘 맞는다")


class TimetableResult(BaseModel):
    timetables: list[Timetable] = Field(description="점수가 높은 순")
    message: str | None = Field(default=None, description="시간표가 없을 때의 이유와 제안")
    truncated: bool = Field(
        default=False, description="경우의 수가 너무 많아 일부만 탐색했는지"
    )


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class ChatRequest(BaseModel):
    """시간표 화면의 채팅 한 번. 예: '세계의 문화 추가해줘', '운영체제 빼줘'"""

    message: str = Field(min_length=1, max_length=500, description="사용자가 입력한 말")
    request: TimetableRequest = Field(description="지금 적용된 조건")
    history: list[ChatMessage] = Field(default_factory=list, description="이전 대화 (최근 것만)")
    current_course_ids: list[str] = Field(
        default_factory=list, description="지금 화면에 보이는 시간표의 강좌번호"
    )


class ChatResponse(BaseModel):
    reply: str = Field(description="채팅창에 보여 줄 답")
    applied: bool = Field(description="조건이 바뀌어 시간표를 다시 만들었는지")
    request: TimetableRequest = Field(description="적용된 조건 (바뀌지 않았으면 보낸 그대로)")
    result: TimetableResult | None = Field(default=None, description="다시 만든 시간표")


# ---------- 에이전트 도구 정의 v3.2: generate_timetable ----------
# 프론트엔드(frontend/app/lib/planning.ts 의 PlanningConstraints)와 같은 필드 이름을 쓴다.

PLAN_DAYS = ("월", "화", "수", "목", "금", "토", "일")


class DayTime(BaseModel):
    day: str = Field(description="요일 한 글자: 월 화 수 목 금 토 일")
    start: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$|^24:00$", description="HH:MM")
    end: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$|^24:00$", description="HH:MM")

    @model_validator(mode="after")
    def _check(self) -> "DayTime":
        if self.day not in PLAN_DAYS:
            raise ValueError("day 는 월~일 중 한 글자여야 합니다")
        if self.start >= self.end:
            raise ValueError("end 는 start 보다 늦어야 합니다")
        return self


class GenerateTimetableRequest(BaseModel):
    """시간표 생성 요청 (v3.2). 반드시 지킬 조건과 가능하면 지킬 조건을 나눠 받는다."""

    base_candidate_id: str | None = Field(
        default=None, description="이 후보(tt_001 등)를 바탕으로 고친다. 그 후보의 과목을 가능하면 유지한다"
    )
    min_credits: float = Field(default=15, ge=0, le=30)
    target_credits: float = Field(default=18, ge=0, le=30)
    max_credits: float = Field(default=19, ge=0, le=30, description="학칙 상한(기본 19)을 넘으면 상한으로 줄인다")
    credits_strict: bool = Field(default=False, description="True 면 최소 학점을 반드시 지킨다")
    free_days: list[str] = Field(default_factory=list, description="반드시 비울 요일")
    blocked_times: list[DayTime] = Field(default_factory=list, description="반드시 비울 시간")
    avoid_times: list[DayTime] = Field(default_factory=list, description="가능하면 비울 시간")
    must_include: list[str] = Field(default_factory=list, description="반드시 넣을 과목. 과목코드, 강좌번호(분반), 과목명")
    exclude: list[str] = Field(default_factory=list, description="넣지 않을 과목. 과목코드, 강좌번호(분반), 과목명")
    ge_areas: list[str] = Field(default_factory=list, description="가능하면 넣을 교양 영역. 예: 인문, 자연, 첨성인기초")
    prefer_professor: list[str] = Field(default_factory=list, description="가능하면 넣을 교수")
    # v3.2 정의서 밖의 확장: 학생 정보 (서버에 저장하지 않는다)
    track: str | None = Field(
        default=None, description="학생 트랙: advanced(심컴) ai(인컴) research(첨컴) platform(플솦) global(글솦)"
    )
    completed: list[str] = Field(default_factory=list, description="이미 이수한 과목코드")
    grade: int | None = Field(default=None, ge=1, le=6, description="학생 학년. 그 학년 과목을 우선한다")
    max_candidates: int = Field(default=3, ge=1, le=5)

    @model_validator(mode="after")
    def _check(self) -> "GenerateTimetableRequest":
        if not self.min_credits <= self.target_credits <= self.max_credits:
            raise ValueError("min_credits <= target_credits <= max_credits 여야 합니다")
        if any(day not in PLAN_DAYS for day in self.free_days):
            raise ValueError("free_days 는 월~일 중 한 글자여야 합니다")
        return self


class Candidate(BaseModel):
    id: str = Field(description="후보 id. tt_001, 대안은 tt_alt_001")
    sections: list[Course] = Field(description="담긴 분반. category 와 area 는 요청의 트랙 기준")
    total_credits: float
    credits_by_category: dict[str, float]
    free_days: list[str]
    gap_minutes: int
    score: float
    warnings: list[str] = Field(default_factory=list, description="정원 초과, 피할 시간과 겹침 등")


OmitReason = Literal[
    "not_offered", "already_completed", "excluded", "not_recommended",
    "free_day_conflict", "blocked_time", "time_conflict",
]


class OmittedCourse(BaseModel):
    item: str = Field(description="요청에 적힌 그대로")
    code: str | None = None
    name: str | None = None
    reason: OmitReason
    detail: str = Field(description="사람이 읽을 이유")


class Alternative(BaseModel):
    id: str
    relaxed: list[str] = Field(description="풀어 준 조건")
    description: str = Field(description="예: 화요일 09:00~12:00 수업을 허용하면 18학점 (컴퓨터구조 포함)")
    candidate: Candidate


class GenerateTimetableResponse(BaseModel):
    status: Literal["success", "partial", "infeasible"] = Field(
        description="success: 반드시 조건과 최소 학점을 모두 지킴, partial: 일부만 지킴, infeasible: 시간표 없음"
    )
    optimal: bool = Field(default=False, description="최적임을 증명했는지. 지금은 항상 False")
    candidates: list[Candidate]
    applied: dict = Field(description="실제로 쓴 학점 조건과 트랙 등")
    omitted_required: list[OmittedCourse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    alternatives: list[Alternative] = Field(default_factory=list, description="조건을 하나 풀면 나아지는 안 (최대 2개)")
