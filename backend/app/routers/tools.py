"""에이전트 도구 정의 v3.2 를 따르는 API. 프론트엔드(Plann)와 이후 Claude 연동이 이 API 를 쓴다."""

import logging

from fastapi import APIRouter, HTTPException

from app.agent import plan_chat
from app.schemas import Candidate, GenerateTimetableRequest, GenerateTimetableResponse
from app.services import planner
from app.services.course_repository import load_courses

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools", tags=["tools (v3.2)"])


@router.post("/generate_timetable", response_model=GenerateTimetableResponse)
def generate_timetable(request: GenerateTimetableRequest) -> GenerateTimetableResponse:
    """조건에 맞는 시간표 후보를 최대 3개 만든다. 일부만 지킬 수 있으면 이유와 대안을 함께 돌려준다."""
    return planner.generate(request, load_courses())


@router.get("/candidates/{candidate_id}", response_model=Candidate)
def get_candidate(candidate_id: str) -> Candidate:
    """앞서 만든 후보(tt_001, tt_alt_001 등)를 다시 가져온다. 대안을 고르면 새로 풀지 않고 이것을 쓴다."""
    candidate = planner.store.get(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="후보를 찾지 못했습니다. 서버를 다시 켜면 후보가 지워집니다.")
    return candidate


@router.post("/chat", response_model=plan_chat.PlanChatResponse)
def chat(request: plan_chat.PlanChatRequest) -> plan_chat.PlanChatResponse:
    """나의 시간표 챗봇. message 가 없으면 지금 후보(candidate_id)를 왜 이렇게 짰는지 설명하고,
    있으면 말대로 조건을 고쳐 그 후보를 바탕으로 다시 만든다."""
    try:
        return plan_chat.handle(request, load_courses())
    except Exception as error:  # AI 호출 실패 (키 오류, 한도 초과, 네트워크 등)
        logger.exception("챗봇 처리 실패. 규칙으로 다시 시도한다")
        try:  # AI 가 안 되면 규칙으로라도 처리한다 (설명도 템플릿으로)
            return plan_chat.handle(request, load_courses(), ask=lambda *_: None)
        except Exception:
            logger.exception("규칙 처리도 실패")
        raise HTTPException(status_code=502, detail="챗봇이 답하지 못했습니다. 잠시 뒤 다시 시도해 주세요.") from error
