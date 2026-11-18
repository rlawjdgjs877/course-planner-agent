"""경북대 이수 과목 불러오기 (실험 기능): 서버가 띄운 브라우저로 학교 화면을 자동 조작한다.

학교의 공식 API 연동이 아니다. 학생이 원격 화면에서 직접 로그인하면 '이수성적 조회' 메뉴로
이동을 시도하고, 학교가 보내는 조회 응답에서 과목 목록만 읽는다.

지키는 것
- 사용자마다 브라우저 컨텍스트(쿠키, 저장소)를 따로 만들고, 추측할 수 없는 토큰으로 구분한다.
- 비밀번호, 쿠키, 세션, 성적 원문, 화면 캡처를 파일이나 로그에 남기지 않는다.
  읽은 과목(코드, 이름, 학점, 이수구분)만 메모리에 두었다가 연결을 닫으면 지운다.
- 연결 종료, 일정 시간 미사용, 최대 사용 시간 초과 시 컨텍스트를 닫는다.
- 원격 브라우저가 허용한 주소(기본 knu.ac.kr) 밖으로 이동하지 못하게 막는다.

Playwright 는 서버의 이벤트 루프와 별개인 전용 스레드에서 돌린다. Windows 에서 서버 루프가
하위 프로세스를 못 띄우는 설정이어도 브라우저를 실행할 수 있게 하기 위해서다.
"""

import asyncio
import base64
import hashlib
import json
import logging
import importlib.util
import os
import re
import secrets
import sys
import threading
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from app.schemas import ImportedCourse, KnuInput
from app.services.knu_transcript import RESPONSE_MARKER, extract_courses

DEFAULT_START_URL = "https://knuin.knu.ac.kr/webview/main/Main.knu"
VIEWPORT = {"width": 1280, "height": 800}
TARGET_TEXT = re.compile(r"^\s*(기?이수\s*성적|전체\s*성적|성적)\s*조회\s*$")  # 띄어쓰기가 달라도 찾는다
PARENT_MENUS = ("학사행정", "수업/성적", "성적")
QUERY_TEXT = re.compile(r"^\s*조회\s*$")
logger = logging.getLogger("app.knu_import")
if not logger.handlers:  # uvicorn 은 앱 로그를 INFO 로 보여 주지 않아서 직접 붙인다
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
LOGIN_TEXT = re.compile(r"^\s*로그인\s*$")
LOGIN_ID_INPUTS ="input[type=text], input[type=email], input:not([type])"  # 아이디 칸 후보
ALLOWED_KEYS = {
    "Enter", "Backspace", "Tab", "Shift+Tab", "Delete", "Escape", "Home", "End",
    "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "PageUp", "PageDown",
}
NAV_INTERVAL = 0.3  # 자동 이동이 화면을 확인하는 간격(초)
NAV_PAUSE_AFTER_TYPING = 1.0  # 학생이 글자를 치는 중이면 이만큼 자동 이동을 쉰다 (클릭은 쉬지 않는다)
TARGET_CLICK_LIMIT = 3  # 이수성적 조회를 이만큼 눌러도 응답이 없으면 자동 이동을 멈춘다
QUERY_CLICK_LIMIT = 2
MENU_CLICK_LIMIT = 4  # 상위 메뉴를 이만큼 눌러도 이수성적 조회가 안 보이면 학생에게 화면을 넘긴다
MENU_HINT = re.compile(r"성적|이수")  # 이수성적 조회 화면에서 '조회' 버튼을 누르는 최대 횟수
WAIT_AFTER_MENU = 0.6  # 상위 메뉴를 누른 뒤 하위 메뉴가 그려지기를 기다리는 시간(초)
WAIT_AFTER_TARGET = 1.0  # 이수성적 조회를 연 뒤 학교가 스스로 목록을 보내는지 기다리는 시간(초)
WAIT_AFTER_QUERY = 3.0  # 조회 버튼을 누른 뒤 응답을 기다리는 시간(초)
PARENT_RETRY = 15.0  # 상위 메뉴를 누르고 이만큼 지나도 못 찾으면 다시 눌러 본다
SETTLE_AFTER_NAVIGATION = 0.5  # 화면이 바뀐 뒤 다 그려지기를 기다리는 시간(초)
NOTICE_SECONDS = 4.0  # 중요한 안내를 보여 주는 최소 시간
BROWSER_KEEP_SECONDS = 600  # 마지막 연결이 끝나도 Chrome 을 이만큼 켜 두어 다음 시작을 빠르게 한다
REAP_INTERVAL = 15.0


class KnuImportError(Exception):
    """사용자에게 그대로 보여 줄 수 있는 오류."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return max(1, int(os.environ.get(name, "")))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    enabled: bool
    allow_remote: bool
    start_url: str
    allowed_hosts: tuple[str, ...]
    channel: str
    max_sessions: int
    idle_seconds: int
    max_seconds: int


def settings() -> Settings:
    """환경변수에서 설정을 읽는다. backend/.env 에 적어도 된다."""
    start_url = os.environ.get("KNU_IMPORT_START_URL") or DEFAULT_START_URL
    hosts = os.environ.get("KNU_IMPORT_ALLOWED_HOSTS") or "knu.ac.kr"
    allowed = {host.strip().lower() for host in hosts.split(",") if host.strip()}
    allowed.add((urlsplit(start_url).hostname or "").lower())
    return Settings(
        enabled=_flag("KNU_IMPORT_ENABLED"),
        allow_remote=_flag("KNU_IMPORT_ALLOW_REMOTE"),
        start_url=start_url,
        allowed_hosts=tuple(sorted(host for host in allowed if host)),
        channel=os.environ.get("KNU_IMPORT_BROWSER_CHANNEL", "chrome").strip(),
        max_sessions=_int("KNU_IMPORT_MAX_SESSIONS", 3),
        idle_seconds=_int("KNU_IMPORT_IDLE_SECONDS", 600),
        max_seconds=_int("KNU_IMPORT_MAX_SECONDS", 1800),
    )


def playwright_installed() -> bool:
    return importlib.util.find_spec("playwright") is not None


def host_allowed(host: str, allowed: tuple[str, ...]) -> bool:
    host = host.lower()
    return any(host == item or host.endswith("." + item) for item in allowed)


@dataclass
class KnuSession:
    token: str
    context: Any
    created: float = field(default_factory=time.monotonic)
    last_seen: float = field(default_factory=time.monotonic)
    last_typing: float = 0.0
    page: Any = None
    status: str = "학교 화면을 여는 중입니다."
    finished: bool = False
    closed: bool = False
    login_visible: bool = False  # 학교 로그인 칸(비밀번호 칸)이 보이는지
    login_at: float = 0.0  # 로그인 칸이 사라진 시각 (걸린 시간 기록용)
    courses: list[ImportedCourse] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    visited_menus: dict[str, float] = field(default_factory=dict)  # 상위 메뉴를 마지막으로 누른 시각
    target_clicks: int = 0
    menu_clicks: int = 0
    query_clicks: int = 0
    wait_until: float = 0.0  # 이 시각까지는 방금 누른 것의 결과를 기다린다
    notice_until: float = 0.0  # 이 시각까지는 중요한 안내를 진행 문구로 덮지 않는다
    last_navigation: float = 0.0  # 마지막으로 화면(페이지)이 바뀐 시각
    nav_task: asyncio.Task | None = None
    last_frame: bytes | None = None
    frame_id: str | None = None
    frame_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    input_lock: asyncio.Lock = field(default_factory=asyncio.Lock)


BrowserFactory = Callable[[Settings], Awaitable[tuple[Callable[[], Awaitable[None]] | None, Any]]]


async def launch_chrome(cfg: Settings) -> tuple[Callable[[], Awaitable[None]], Any]:
    """Chrome 을 화면 없이 띄운다. 설치된 Chrome 이 없으면 Playwright 의 Chromium 을 쓴다."""
    from playwright.async_api import async_playwright

    playwright = await async_playwright().start()
    for channel in dict.fromkeys([cfg.channel, ""]):
        try:
            browser = await playwright.chromium.launch(channel=channel or None, headless=True)
            break
        except Exception:
            continue
    else:
        await playwright.stop()
        raise KnuImportError(
            503,
            "브라우저를 실행하지 못했습니다. Google Chrome 을 설치하거나 "
            "'python -m playwright install chromium' 을 실행해 주세요.",
        )

    async def close() -> None:
        await browser.close()
        await playwright.stop()

    return close, browser


class _Worker:
    """Playwright 전용 스레드와 이벤트 루프."""

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._lock = threading.Lock()

    def loop(self) -> asyncio.AbstractEventLoop:
        with self._lock:
            if self._loop is None or self._loop.is_closed():
                ready = threading.Event()

                def run() -> None:
                    # Proactor 루프여야 Windows 에서 브라우저 프로세스를 띄울 수 있다.
                    loop = asyncio.ProactorEventLoop() if sys.platform == "win32" else asyncio.new_event_loop()
                    self._loop = loop
                    ready.set()
                    loop.run_forever()

                threading.Thread(target=run, name="knu-import-browser", daemon=True).start()
                ready.wait()
            return self._loop

    @property
    def running(self) -> bool:
        return self._loop is not None and self._loop.is_running()

    async def run(self, coroutine: Awaitable[Any]) -> Any:
        future = asyncio.run_coroutine_threadsafe(coroutine, self.loop())
        return await asyncio.wrap_future(future)

    def run_blocking(self, coroutine: Awaitable[Any], timeout: float) -> Any:
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop()).result(timeout)


class KnuSessionManager:
    def __init__(self, browser_factory: BrowserFactory = launch_chrome) -> None:
        self._factory = browser_factory
        self._worker = _Worker()
        self._sessions: dict[str, KnuSession] = {}
        self._browser: Any = None
        self._close_browser: Callable[[], Awaitable[None]] | None = None
        self._reaper: asyncio.Task | None = None
        self._idle_since = 0.0  # 마지막 연결이 끝난 시각
        self._launch_lock: asyncio.Lock | None = None

    # ---------- 서버(FastAPI) 쪽에서 부르는 함수 ----------

    async def start(self) -> str:
        return await self._worker.run(self._start(settings()))

    async def frame(self, token: str, have: str | None = None, image: bool = True) -> dict:
        return await self._worker.run(self._frame(token, have, image))

    async def send_input(self, token: str, action: KnuInput) -> None:
        await self._worker.run(self._send_input(token, action))

    async def retry_navigation(self, token: str) -> None:
        await self._worker.run(self._retry(token))

    async def login(self, token: str, user_id: str, password: str, submit: bool = True) -> None:
        await self._worker.run(self._login(token, user_id, password, submit))

    async def stop(self, token: str) -> bool:
        return await self._worker.run(self._stop(token))

    def warm(self) -> None:
        """Chrome 을 미리 띄워 둔다. 학생이 안내를 읽는 동안 준비해서 첫 연결을 빠르게 한다."""
        asyncio.run_coroutine_threadsafe(self._warm(settings()), self._worker.loop())

    def session_count(self) -> int:
        return len(self._sessions)

    def shutdown(self) -> None:
        """서버를 끌 때 모든 브라우저를 닫는다."""
        if self._worker.running:
            try:
                self._worker.run_blocking(self._close_all(), timeout=15)
            except Exception:
                pass

    # ---------- 아래는 모두 Playwright 스레드에서 돈다 ----------

    def _get(self, token: str) -> KnuSession:
        session = self._sessions.get(token) if token else None
        if session is None or session.closed:
            raise KnuImportError(404, "연결이 끝났습니다. 다시 시작해 주세요.")
        return session

    async def _start(self, cfg: Settings) -> str:
        await self._reap(cfg)
        if len(self._sessions) >= cfg.max_sessions:
            raise KnuImportError(429, "지금은 연결이 가득 찼습니다. 잠시 뒤 다시 시도해 주세요.")
        await self._ensure_browser(cfg)

        context = await self._browser.new_context(
            viewport=VIEWPORT, locale="ko-KR", accept_downloads=False, service_workers="block"
        )
        session = KnuSession(token=secrets.token_urlsafe(32), context=context)
        self._sessions[session.token] = session

        context.on("response", lambda response: self._on_response(session, response))
        context.on("request", lambda request: self._on_request(session, request))
        context.on("page", lambda page: self._on_page(session, cfg, page))
        try:
            page = await context.new_page()
            await self._guard_page(session, cfg, page)
        except Exception as error:
            await self._close(session)
            raise KnuImportError(502, "브라우저 화면을 준비하지 못했습니다. 다시 시도해 주세요.") from error
        session.page = page

        # 학교 페이지가 다 열릴 때까지 기다리지 않고 바로 돌려준다. 여는 동안의 화면도 보여 준다.
        session.nav_task = asyncio.create_task(self._open_school(session, cfg))
        if self._reaper is None or self._reaper.done():
            self._reaper = asyncio.create_task(self._reap_loop(cfg))
        return session.token

    async def _ensure_browser(self, cfg: Settings) -> None:
        if self._launch_lock is None:
            self._launch_lock = asyncio.Lock()
        async with self._launch_lock:  # 미리 띄우기와 연결 시작이 겹쳐도 Chrome 은 하나만 띄운다
            if self._browser is not None and not getattr(self._browser, "is_connected", lambda: True)():
                await self._shutdown_browser()  # Chrome 이 꺼져 있으면 새로 띄운다
            if self._browser is None:
                self._close_browser, self._browser = await self._factory(cfg)
                self._idle_since = time.monotonic()
        if self._reaper is None or self._reaper.done():
            self._reaper = asyncio.create_task(self._reap_loop(cfg))

    async def _warm(self, cfg: Settings) -> None:
        try:
            await self._ensure_browser(cfg)
        except Exception:
            pass  # 실패해도 연결을 시작할 때 다시 시도한다

    async def _open_school(self, session: KnuSession, cfg: Settings) -> None:
        try:
            await session.page.goto(cfg.start_url, wait_until="domcontentloaded", timeout=30_000)
        except Exception:
            if not session.closed:
                session.status = "학교 화면을 열지 못했습니다. 인터넷 연결을 확인하고, 연결을 종료한 뒤 다시 시도해 주세요."
            return
        session.status = "학교 화면에서 직접 로그인해 주세요. 로그인하면 이수성적 조회까지 자동으로 이동합니다."
        await self._auto_navigate(session)

    def _on_page(self, session: KnuSession, cfg: Settings, page: Any) -> None:
        # 학교가 새 창을 열면 그 창을 보여 주고, 그 창의 화면 이동도 검사한다.
        if not session.closed:
            session.page = page
            asyncio.ensure_future(self._guard_page(session, cfg, page))

    def _active_page(self, session: KnuSession) -> Any:
        if session.page is not None and not session.page.is_closed():
            return session.page
        if session.context is None:  # 과목을 다 읽어 브라우저를 닫았다
            return None
        pages = [page for page in session.context.pages if not page.is_closed()]
        session.page = pages[-1] if pages else None
        return session.page

    def _blocked(self, session: KnuSession, cfg: Settings, url: str) -> bool:
        """허용하지 않은 주소면 True. 상태 줄에 막았다고 알린다."""
        if not url.startswith(("http://", "https://")):
            return False
        host = urlsplit(url).hostname or ""
        if host_allowed(host, cfg.allowed_hosts):
            return False
        session.status = f"학교 밖 주소({host})로 이동해서 이전 화면으로 되돌렸습니다."
        session.notice_until = time.monotonic() + NOTICE_SECONDS
        return True

    async def _guard_page(self, session: KnuSession, cfg: Settings, page: Any) -> None:
        """원격 브라우저가 허용한 주소 밖에 머물지 못하게 한다.

        요청을 미리 가로채는 방식(Playwright route, Chrome Fetch)은 켜는 것만으로 파일이 많은
        페이지를 50% 이상 느리게 만들어서 쓰지 않는다. 대신 화면이 밖의 주소로 바뀌면 곧바로
        이전 화면으로 되돌리거나, 새 창이면 닫는다.
        """
        page.on("framenavigated", lambda frame: self._after_navigation(session, cfg, page, frame))

    def _after_navigation(self, session: KnuSession, cfg: Settings, page: Any, frame: Any) -> None:
        """화면이 학교 밖 주소로 바뀌었으면 되돌린다."""
        if session.closed or frame != page.main_frame:
            return
        session.last_navigation = time.monotonic()
        if not self._blocked(session, cfg, frame.url):
            return
        asyncio.ensure_future(self._leave(session, page))

    async def _leave(self, session: KnuSession, page: Any) -> None:
        try:
            pages = session.context.pages
            if pages and page is not pages[0]:
                await page.close()  # 새 창이면 닫는다
            else:
                await page.go_back()
        except Exception:
            pass

    async def _on_response(self, session: KnuSession, response: Any) -> None:
        if session.closed or RESPONSE_MARKER not in response.url:
            return
        try:
            courses, duplicates = extract_courses(await response.json())
        except Exception:
            # 응답 내용은 남기지 않는다. 형식이 다르면 화면에서 직접 확인하도록 안내만 한다.
            session.status = "조회 응답을 읽지 못했습니다. 아래에서 직접 입력하거나 붙여넣기로 추가해 주세요."
            return
        session.courses, session.duplicates = courses, duplicates
        session.finished = True
        session.status = f"이수 과목 {len(courses)}개를 읽었습니다. 아래 목록을 확인해 주세요."
        self._log(session, f"과목 {len(courses)}개 읽음")
        # 다 읽었으면 학교 세션(쿠키)을 담은 브라우저는 바로 닫는다. 읽은 과목은 연결을 끊을 때까지 둔다.
        asyncio.ensure_future(self._release(session))

    async def _release(self, session: KnuSession) -> None:
        if session.nav_task is not None and session.nav_task is not asyncio.current_task():
            session.nav_task.cancel()
        context, session.context, session.page = session.context, None, None
        try:
            if context is not None:
                await context.close()
        except Exception:
            pass

    @staticmethod
    def _log(session: KnuSession, step: str) -> None:
        """자동 이동 단계별 걸린 시간 (단계 이름만, 입력값·학번·성적은 남기지 않는다)."""
        base = session.login_at or session.created
        logger.info("knu-import %s +%.1fs %s", session.token[:6], time.monotonic() - base, step)

    def _on_request(self, session: KnuSession, request: Any) -> None:
        """학교 조회 요청의 모양만 남긴다: 주소 경로, 헤더 이름, 본문 키 이름 (값은 남기지 않는다)."""
        if session.closed or RESPONSE_MARKER not in request.url:
            return
        try:
            body = request.post_data or ""
            try:
                parsed = json.loads(body)
                keys = {k: sorted(v) if isinstance(v, dict) else type(v).__name__ for k, v in parsed.items()}
            except Exception:
                keys = sorted({k for k, _ in parse_qsl(body, keep_blank_values=True)})
            logger.info(
                "knu-import request shape: %s %s headers=%s body_keys=%s",
                request.method, urlsplit(request.url).path, sorted(request.headers), keys,
            )
        except Exception:
            pass

    def _pages(self, session: KnuSession) -> list[Any]:
        """열려 있는 모든 창. 지금 보여 주는 창을 먼저 살핀다."""
        if session.context is None:
            return []
        active = self._active_page(session)
        pages = [page for page in session.context.pages if not page.is_closed()]
        return ([active] if active in pages else []) + [page for page in pages if page is not active]

    async def _find(self, session: KnuSession, locate: Callable[[Any], Any]) -> tuple[Any, Any]:
        """모든 창의 모든 프레임에서 처음 보이는 요소를 찾는다. (창, 요소) 또는 (None, None)."""
        for page in self._pages(session):
            for frame in page.frames:
                try:
                    items = locate(frame)
                    for index in range(min(await items.count(), 10)):
                        candidate = items.nth(index)
                        if await candidate.is_visible():
                            return page, candidate
                except Exception:
                    continue
        return None, None

    @staticmethod
    def _query_button(frame: Any) -> Any:
        return frame.get_by_role("button", name=QUERY_TEXT).or_(frame.get_by_text(QUERY_TEXT))

    async def _click(self, session: KnuSession, page: Any, element: Any, status: str, wait: float) -> None:
        session.page = page  # 자동으로 누른 창을 보여 줘서 학생이 진행 상황을 볼 수 있게 한다
        session.status = status
        session.wait_until = time.monotonic() + wait
        self._log(session, status)
        await element.click(timeout=1500)

    async def _navigate_step(self, session: KnuSession) -> bool:
        """메뉴를 한 단계 누른다. 자동 이동을 그만둬야 하면 True."""
        now = time.monotonic()
        if now < session.wait_until:
            return False  # 방금 누른 것의 결과를 기다린다
        if now - session.last_navigation < SETTLE_AFTER_NAVIGATION:
            return False  # 화면이 막 바뀌어 아직 그리는 중일 수 있다 (로그인 칸이 늦게 나타나는 경우)

        # 비밀번호 칸이 보이면 아직 로그인 전이다. 로그인 화면의 메뉴를 미리 누르지 않는다.
        page, _ = await self._find(session, lambda frame: frame.locator("input[type=password]"))
        if session.login_visible and page is None and not session.login_at:
            session.login_at = now
            self._log(session, "로그인 끝")
        session.login_visible = page is not None
        if page is not None:
            if not session.target_clicks:
                self._info(session, "학교 화면에서 로그인해 주세요. 로그인하면 이수성적 조회까지 자동으로 이동합니다.")
            return False

        # 이수성적 조회 화면을 열었는데 응답이 없으면 '조회' 버튼을 누른다.
        if session.target_clicks and session.query_clicks < QUERY_CLICK_LIMIT:
            page, button = await self._find(session, self._query_button)
            if button is not None:
                session.query_clicks += 1
                await self._click(session, page, button, "조회 버튼을 눌러 이수 과목을 불러오는 중입니다.", WAIT_AFTER_QUERY)
                return False

        page, target = await self._find(session, lambda frame: frame.get_by_text(TARGET_TEXT))
        if target is not None:
            if session.target_clicks >= TARGET_CLICK_LIMIT:
                session.status = (
                    "이수성적 조회를 여러 번 열었지만 응답을 받지 못해 자동 이동을 멈췄습니다. "
                    "화면에서 직접 조회 버튼을 누르거나 '자동 이동 다시 시도'를 눌러 주세요."
                )
                return True
            session.target_clicks += 1
            session.query_clicks = 0
            await self._click(session, page, target, "이수성적 조회 화면을 여는 중입니다.", WAIT_AFTER_TARGET)
            return False

        if session.menu_clicks >= MENU_CLICK_LIMIT:
            # 메뉴 이름이 예상과 다르다. 계속 돌지 말고 학생에게 화면을 넘긴다 (직접 눌러도 응답은 읽는다).
            await self._log_menu_labels(session)
            session.status = (
                "이수성적 조회 메뉴를 자동으로 찾지 못했습니다. 화면에서 이수성적 조회 메뉴를 직접 눌러 주세요. "
                "목록이 뜨면 과목을 바로 읽습니다."
            )
            return True

        for label in PARENT_MENUS:
            if now - session.visited_menus.get(label, float("-inf")) < PARENT_RETRY:
                continue
            page, menu = await self._find(session, lambda frame, label=label: frame.get_by_text(label, exact=True))
            if menu is None:
                continue
            session.visited_menus[label] = now
            session.menu_clicks += 1
            await self._click(session, page, menu, f"'{label}' 메뉴에서 이수성적 조회를 찾고 있습니다.", WAIT_AFTER_MENU)
            return False

        if not session.target_clicks:
            self._info(session, "이수성적 조회 메뉴를 찾고 있습니다. 화면에 보이면 직접 눌러도 됩니다.")
        return False

    async def _log_menu_labels(self, session: KnuSession) -> None:
        """화면에 보이는 메뉴 이름 중 '성적'·'이수'가 들어간 것만 남긴다 (메뉴 이름이라 개인 정보가 아니다)."""
        labels: set[str] = set()
        for page in self._pages(session):
            for frame in page.frames:
                try:
                    texts = await frame.locator("a, li, span, button").filter(has_text=MENU_HINT).all_inner_texts()
                    labels.update(t.strip() for t in texts if 0 < len(t.strip()) <= 20)
                except Exception:
                    continue
        self._log(session, f"메뉴를 못 찾음. 보이는 메뉴 후보: {sorted(labels)[:40]}")

    @staticmethod
    def _info(session: KnuSession, text: str) -> None:
        """기다리는 중이라는 문구. 막 보여 준 중요한 안내(학교 밖 이동 등)는 덮지 않는다."""
        if time.monotonic() >= session.notice_until:
            session.status = text

    async def _auto_navigate(self, session: KnuSession) -> None:
        # 메뉴가 보이지 않는 동안(로그인, 추가 인증 중)에는 기다리기만 한다.
        # 오래 걸려도 연결은 미사용 시간과 최대 사용 시간으로 정리된다.
        while not session.closed and not session.finished:
            await asyncio.sleep(NAV_INTERVAL)
            if time.monotonic() - session.last_typing < NAV_PAUSE_AFTER_TYPING:
                continue  # 학생이 글자를 치는 중에는 화면을 건드리지 않는다
            try:
                if await self._navigate_step(session):
                    return
            except Exception:
                session.status = "자동 이동을 시도하고 있습니다. 메뉴가 보이지 않으면 화면에서 직접 선택해 주세요."

    async def _retry(self, token: str) -> None:
        session = self._get(token)
        session.last_seen = time.monotonic()
        if session.finished:
            return
        session.visited_menus.clear()
        session.target_clicks = session.query_clicks = session.menu_clicks = 0
        session.wait_until = 0.0
        session.status = "자동 이동을 다시 시도합니다."
        if session.nav_task is None or session.nav_task.done():
            session.nav_task = asyncio.create_task(self._auto_navigate(session))

    async def _frame(self, token: str, have: str | None = None, image: bool = True) -> dict:
        session = self._get(token)
        session.last_seen = time.monotonic()
        page = self._active_page(session) if image else None
        if page is not None and not session.frame_lock.locked():
            async with session.frame_lock:
                try:
                    session.last_frame = await page.screenshot(type="jpeg", quality=55, timeout=5000)
                    session.frame_id = hashlib.blake2b(session.last_frame, digest_size=8).hexdigest()
                except Exception:
                    pass  # 이번 캡처를 건너뛰고 직전 화면을 보여 준다
        cfg = settings()
        now = time.monotonic()
        expires = min(cfg.idle_seconds, cfg.max_seconds - (now - session.created))
        return {
            # 학생 화면에 이미 있는 것과 같으면 이미지를 다시 보내지 않는다.
            "image": base64.b64encode(session.last_frame).decode()
            if image and session.last_frame and session.frame_id != have
            else None,
            "frame_id": session.frame_id,
            "status": session.status,
            "finished": session.finished,
            "login_form": session.login_visible and not session.finished,
            "courses": session.courses,
            "duplicates": session.duplicates,
            "expires_in": max(0, int(expires)),
        }

    async def _send_input(self, token: str, action: KnuInput) -> None:
        session = self._get(token)
        session.last_seen = time.monotonic()
        if action.type in ("text", "key"):
            session.last_typing = session.last_seen
        page = self._active_page(session)
        if page is None:
            raise KnuImportError(409, "학교 화면이 닫혔습니다. 연결을 종료하고 다시 시작해 주세요.")
        async with session.input_lock:
            if action.type == "click" and action.x is not None and action.y is not None:
                await page.mouse.click(action.x, action.y)
            elif action.type == "key" and action.key in ALLOWED_KEYS:
                await page.keyboard.press(action.key)
            elif action.type == "text" and action.text:
                await page.keyboard.insert_text(action.text)
            elif action.type == "scroll" and action.delta is not None:
                await page.mouse.wheel(0, action.delta)
            else:
                raise KnuImportError(400, "보낼 수 없는 입력입니다.")

    async def _login(self, token: str, user_id: str, password: str, submit: bool) -> None:
        """보이는 비밀번호 칸과 같은 프레임의 첫 글자 칸에 값을 채우고, 로그인 버튼(없으면 Enter)으로 제출한다.

        값은 이 함수 안에서만 쓰고 세션에도 남기지 않는다.
        """
        session = self._get(token)
        session.last_seen = time.monotonic()
        async with session.input_lock:
            for page in self._pages(session):
                for frame in page.frames:
                    try:
                        pw = await self._first_visible(frame.locator("input[type=password]"))
                        if pw is None:
                            continue
                        uid = await self._first_visible(frame.locator(LOGIN_ID_INPUTS))
                        if uid is None:
                            continue
                        await uid.fill(user_id, timeout=2000)
                        await pw.fill(password, timeout=2000)
                        session.page = page
                        if submit:
                            session.status = "로그인하는 중입니다. 로그인하면 이수성적 조회까지 자동으로 이동합니다."
                            button = await self._first_visible(frame.get_by_role("button", name=LOGIN_TEXT))
                            if button is not None:
                                await button.click(timeout=2000)
                            else:
                                await pw.press("Enter", timeout=2000)
                        return
                    except Exception:
                        continue
        raise KnuImportError(409, "학교 화면에서 로그인 칸을 찾지 못했습니다. 화면을 눌러 직접 입력해 주세요.")

    @staticmethod
    async def _first_visible(items: Any) -> Any:
        for index in range(min(await items.count(), 10)):
            if await items.nth(index).is_visible():
                return items.nth(index)
        return None

    async def _stop(self, token: str) -> bool:
        session = self._sessions.get(token) if token else None
        if session is None:
            return False
        await self._close(session)
        return True

    async def _close(self, session: KnuSession) -> None:
        session.closed = True
        self._sessions.pop(session.token, None)
        if session.nav_task is not None and session.nav_task is not asyncio.current_task():
            session.nav_task.cancel()
        session.courses, session.duplicates, session.last_frame = [], [], None
        try:
            await session.context.close()  # 이 연결의 쿠키와 저장소가 함께 사라진다
        except Exception:
            pass
        session.context = session.page = None
        if not self._sessions:
            self._idle_since = time.monotonic()  # Chrome 은 잠시 켜 두었다가 _reap 에서 닫는다

    async def _shutdown_browser(self) -> None:
        close, self._close_browser, self._browser = self._close_browser, None, None
        if close is not None:
            try:
                await close()
            except Exception:
                pass

    async def _reap(self, cfg: Settings) -> None:
        now = time.monotonic()
        for session in list(self._sessions.values()):
            if now - session.last_seen > cfg.idle_seconds or now - session.created > cfg.max_seconds:
                await self._close(session)
        if not self._sessions and self._browser is not None and now - self._idle_since > BROWSER_KEEP_SECONDS:
            await self._shutdown_browser()

    async def _reap_loop(self, cfg: Settings) -> None:
        while self._sessions or self._browser is not None:
            await asyncio.sleep(REAP_INTERVAL)
            await self._reap(settings())

    async def _close_all(self) -> None:
        for session in list(self._sessions.values()):
            await self._close(session)
        await self._shutdown_browser()


manager = KnuSessionManager()
