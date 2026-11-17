from fastapi import APIRouter, Query

from app.schemas import CourseList, RequirementList
from app.services.course_repository import (
    load_courses,
    load_requirements,
    search_courses,
    using_sample_data,
)

router = APIRouter(tags=["data"])


@router.get("/courses", response_model=CourseList)
def list_courses(
    q: str | None = Query(default=None, description="과목명이나 교과목코드의 일부"),
    category: str | None = Query(default=None, description="교과구분. 예: 교양"),
    department: str | None = Query(default=None, description="개설학과"),
) -> CourseList:
    """개설 강좌. 조건을 주지 않으면 전체를 돌려준다."""
    if q or category or department:
        courses = search_courses(q=q, category=category, department=department)
    else:
        courses = load_courses()
    return CourseList(sample=using_sample_data(), courses=courses)


@router.get("/requirements", response_model=RequirementList)
def list_requirements(
    department: str | None = Query(default=None, description="학과"),
    admission_year: int | None = Query(default=None, description="입학연도"),
) -> RequirementList:
    """졸업 요건. 학과와 입학연도로 좁힐 수 있다."""
    requirements, sample = load_requirements(department, admission_year)
    return RequirementList(sample=sample, requirements=requirements)
