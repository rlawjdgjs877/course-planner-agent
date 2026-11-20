"""Claude API 연결 설정. 채팅(/chat)과 시간표 에이전트(/agent/chat)가 함께 쓴다."""

import os

from dotenv import load_dotenv

DEFAULT_MODEL = "claude-opus-5-5"


class ChatUnavailable(Exception):
    """AI 를 쓸 준비가 안 됐을 때 (API 키가 없음)."""


def model_name() -> str:
    return os.getenv("CLAUDE_MODEL") or DEFAULT_MODEL


def client():
    """Anthropic 클라이언트를 만든다. 키가 없으면 ChatUnavailable."""
    load_dotenv()  # 서버를 켠 뒤 .env 를 만들어도 읽히도록 매번 확인한다
    if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")):
        raise ChatUnavailable(
            "AI 기능을 쓰려면 backend/.env 파일에 ANTHROPIC_API_KEY 를 넣어야 합니다. 시간표 만들기는 키 없이도 동작합니다."
        )
    import anthropic

    return anthropic.Anthropic()
