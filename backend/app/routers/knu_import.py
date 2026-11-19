"""경북대 이수 과목 불러오기 (실험 기능) API.

기본으로 꺼져 있다. KNU_IMPORT_ENABLED=1 일 때만 동작하고, KNU_IMPORT_ALLOW_REMOTE=1 이
아니면 이 컴퓨터에서 온 요청만 받는다. 요청 본문(입력한 글자 등)은 로그에 남기지 않는다.
"""

from urllib.parse import urlsplit

from fastapi import APIRouter, Header, HTTPException, Request

from app.schemas import (
    KnuFrame,
    KnuFrameRequest,
    KnuImportStatus,
    KnuInput,
    KnuLogin,
    KnuStartRequest,
    KnuStartResponse,
    KnuStopRequest,
)
from app.services import knu_session
from app.settings import FRONTEND_ORIGINS

router = APIRouter(prefix="/import/knu", tags=["import"])
LOOPBACK = {"127.0.0.1", "::1", "localhost"}


def _unavailable_reason(request: Request) -> str | None:
    cfg = knu_session.settings()
    if not cfg.enabled:
        return "이 서버에서는 학교 화면 불러오기가 꺼져 있습니다. 직접 입력이나 붙여넣기를 이용해 주세요."
    if not knu_session.playwright_installed():
        return "서버에 Playwright 가 설치되어 있지 않습니다 (pip install -r requirements-import.txt)."
    client = request.client.host if request.client else ""
    if not cfg.allow_remote and client not in LOOPBACK:
        return "학교 화면 불러오기는 서버를 실행한 컴퓨터에서만 쓸 수 있습니다."
    return None


def _check(request: Request) -> None:
    reason = _unavailable_reason(request)
    if reason:
        raise HTTPException(status_code=403 if "컴퓨터에서만" in reason else 503, detail=reason)
    # 다른 사이트가 사용자의 브라우저를 이용해 이 API 를 부르지 못하게 한다.
    origin = request.headers.get("origin")
    if origin and urlsplit(origin).netloc != request.headers.get("host") and origin not in FRONTEND_ORIGINS:
        raise HTTPException(status_code=403, detail="허용되지 않은 요청입니다.")


async def _call(coroutine):
    try:
        return await coroutine
    except knu_session.KnuImportError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from None
    except HTTPException:
        raise
    except Exception:
        # 예외 내용에 입력값이 섞일 수 있어 로그에도, 응답에도 싣지 않는다.
        raise HTTPException(status_code=500, detail="원격 화면 처리 중 문제가 생겼습니다. 다시 시도해 주세요.") from None


@router.get("/status", response_model=KnuImportStatus)
def status(request: Request) -> KnuImportStatus:
    """이 실험 기능을 지금 쓸 수 있는지."""
    cfg = knu_session.settings()
    reason = _unavailable_reason(request)
    if reason is None:
        knu_session.manager.warm()  # 학생이 안내를 읽는 동안 Chrome 을 준비한다
    return KnuImportStatus(
        enabled=cfg.enabled,
        installed=knu_session.playwright_installed(),
        available=reason is None,
        reason=reason,
        idle_minutes=max(1, cfg.idle_seconds // 60),
    )


@router.post("/start", response_model=KnuStartResponse)
async def start(body: KnuStartRequest, request: Request) -> KnuStartResponse:
    """학생 한 명을 위한 원격 브라우저를 띄우고 학교 화면을 연다."""
    _check(request)
    if not body.consent:
        raise HTTPException(status_code=400, detail="안내를 확인하고 동의해야 시작할 수 있습니다.")
    return KnuStartResponse(session=await _call(knu_session.manager.start()))


@router.post("/frame", response_model=KnuFrame)
async def frame(
    request: Request, body: KnuFrameRequest | None = None, x_import_session: str = Header(default="")
) -> KnuFrame:
    """원격 화면 한 장과 진행 상태, 읽은 과목. 화면이 바뀌지 않았으면 이미지는 비워 보낸다."""
    _check(request)
    have = body.have if body else None
    image = body.image if body else True
    return KnuFrame(**await _call(knu_session.manager.frame(x_import_session, have, image)))


@router.post("/input")
async def send_input(body: KnuInput, request: Request, x_import_session: str = Header(default="")) -> dict:
    """원격 화면에 클릭, 키, 글자, 스크롤, 마우스 이동을 보낸다. 이동이면 그 자리의 마우스 모양을 돌려준다."""
    _check(request)
    cursor = await _call(knu_session.manager.send_input(x_import_session, body))
    return {"ok": True, "cursor": cursor}


@router.post("/login")
async def login(body: KnuLogin, request: Request, x_import_session: str = Header(default="")) -> dict:
    """학교 화면의 로그인 칸을 채우고 제출한다. 값은 저장하거나 로그에 남기지 않는다."""
    _check(request)
    await _call(knu_session.manager.login(x_import_session, body.user_id, body.password.get_secret_value()))
    return {"ok": True}


@router.post("/navigate")
async def navigate(request: Request, x_import_session: str = Header(default="")) -> dict:
    """이수성적 조회 메뉴로 자동 이동을 다시 시도한다."""
    _check(request)
    await _call(knu_session.manager.retry_navigation(x_import_session))
    return {"ok": True}


@router.post("/stop")
async def stop(
    request: Request, body: KnuStopRequest | None = None, x_import_session: str = Header(default="")
) -> dict:
    """연결을 끊고 브라우저, 쿠키, 읽은 과목을 지운다."""
    # 끄는 것은 기능이 꺼져 있어도 허용한다. 출처만 확인한다.
    origin = request.headers.get("origin")
    if origin and urlsplit(origin).netloc != request.headers.get("host") and origin not in FRONTEND_ORIGINS:
        raise HTTPException(status_code=403, detail="허용되지 않은 요청입니다.")
    token = x_import_session or (body.session if body else "") or ""
    closed = await _call(knu_session.manager.stop(token)) if token else False
    return {"ok": True, "closed": closed}
