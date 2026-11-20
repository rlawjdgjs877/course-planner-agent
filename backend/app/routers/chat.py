import logging

from fastapi import APIRouter, HTTPException

from app.agent.chat import ChatUnavailable, handle_chat
from app.schemas import ChatRequest, ChatResponse
from app.services.course_repository import load_courses

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """말로 시간표를 고친다. 예: '세계의 문화 추가해줘', '운영체제 빼줘', '금요일 비워줘'"""
    try:
        return handle_chat(request, load_courses())
    except ChatUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:  # Claude 호출 실패 (키 오류, 한도 초과, 네트워크 등)
        logger.exception("chat failed")
        raise HTTPException(
            status_code=502,
            detail="AI 응답을 받지 못했습니다. API 키와 사용 한도를 확인한 뒤 다시 시도하세요.",
        ) from error
