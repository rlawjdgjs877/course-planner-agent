from fastapi import APIRouter

from app.schemas import CourseList
from app.services.course_repository import load_courses, using_sample_data

router = APIRouter(tags=["courses"])


@router.get("/courses", response_model=CourseList)
def list_courses() -> CourseList:
    """이번 학기 개설 강좌 전체를 돌려준다."""
    return CourseList(sample=using_sample_data(), courses=load_courses())
