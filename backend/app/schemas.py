"""과목 데이터 형식.

학교 '수업시간표 및 강의계획서 조회' 화면의 열 구성을 그대로 따른다.
backend/app/data/courses.json 은 Course 의 목록이다.
"""

from pydantic import BaseModel, Field


class Meeting(BaseModel):
    """수업 한 번. 예: 월요일 09:00~10:30"""

    day: str = Field(description="요일 한 글자: 월 화 수 목 금 토 일")
    start: str = Field(description="시작 시각 HH:MM")
    end: str = Field(description="종료 시각 HH:MM")


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
