from fastapi import APIRouter

from app.schemas import TimetableRequest, TimetableResult
from app.services.course_repository import load_courses
from app.services.timetable import generate_timetables

router = APIRouter(tags=["timetables"])


@router.post("/timetables", response_model=TimetableResult)
def create_timetables(request: TimetableRequest) -> TimetableResult:
    """조건에 맞고 시간이 겹치지 않는 시간표를 점수가 높은 순으로 돌려준다."""
    return generate_timetables(load_courses(), request)
