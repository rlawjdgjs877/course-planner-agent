import logging

from fastapi import APIRouter, HTTPException

from app.agent import planner_agent
from app.agent.claude import ChatUnavailable
from app.agent.planner_agent import AgentChatRequest, AgentChatResponse
from app.services.course_repository import load_courses

router = APIRouter(prefix="/agent", tags=["agent"])
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=AgentChatResponse)
def agent_chat(request: AgentChatRequest) -> AgentChatResponse:
    """시간표 에이전트와 한 번 대화한다. mode=summary 면 방금 만든 시간표를 요약한다.

    Claude 가 과목 검색, 시간표 다시 만들기, 선수과목 확인 도구를 골라 쓰고 결과를 설명한다.
    """
    try:
        return planner_agent.handle(request, load_courses())
    except ChatUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:  # Claude 호출 실패 (키 오류, 한도 초과, 네트워크 등)
        logger.exception("agent chat failed")
        raise HTTPException(
            status_code=502,
            detail="AI 응답을 받지 못했습니다. API 키와 사용 한도를 확인한 뒤 다시 시도하세요.",
        ) from error
