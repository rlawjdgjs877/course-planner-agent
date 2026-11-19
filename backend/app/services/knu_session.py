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
import importlib.util
import itertools
import logging
import os
import re
import secrets
import sys
import threading
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit

from app.schemas import ImportedCourse, KnuInput
from app.services.knu_transcript import RESPONSE_MARKER, extract_courses

# 단계별 걸린 시간을 서버 콘솔에 남긴다. 토큰, 입력한 글자, 주소의 경로·쿼리, 과목 내용은 남기지 않는다.
log = logging.getLogger("knu_import")
if not log.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s [knu_import] %(message)s", "%H:%M:%S"))
    log.addHandler(_handler)
    log.setLevel(logging.INFO)
    log.propagate = False
_log_ids = itertools.count(1)

DEFAULT_START_URL = "https://knuin.knu.ac.kr/webview/main/Main.knu"
VIEWPORT = {"width": 1280, "height": 800}
TARGET_TEXT = re.compile(r"^\s*이수\s*성적\s*조회\s*$")  # 띄어쓰기가 달라도 찾는다
# 통합정보시스템 왼쪽 아래 메뉴: 성적 → 학기성적 → 이수성적조회. 이 순서로만 누른다.
MENU_PATH = ("성적", "학기성적")
FALLBACK_MENU = "학사행정"  # '성적'을 여러 번 눌러도 안 펼쳐지면 이 메뉴를 한 번 열어 본다
FALLBACK_AFTER = 3  # '성적'을 이만큼 시도해도 진척이 없으면 FALLBACK_MENU 를 누른다
QUERY_TEXT = re.compile(r"^\s*조회\s*$")
ALLOWED_KEYS = {
    "Enter", "Backspace", "Tab", "Shift+Tab", "Delete", "Escape", "Home", "End",
    "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "PageUp", "PageDown",
}
NAV_INTERVAL = 0.1  # 자동 이동이 화면을 확인하는 간격(초)
NAV_PAUSE_AFTER_TYPING = 1.0  # 학생이 글자를 치는 중이면 이만큼 자동 이동을 쉰다 (클릭은 쉬지 않는다)
TARGET_CLICK_LIMIT = 3  # 이수성적 조회를 이만큼 눌러도 응답이 없으면 자동 이동을 멈춘다
QUERY_CLICK_LIMIT = 2  # 이수성적 조회 화면에서 '조회' 버튼을 누르는 최대 횟수
WAIT_AFTER_MENU = 0.3  # 상위 메뉴를 누른 뒤 하위 메뉴가 그려지기를 기다리는 시간(초)
WAIT_AFTER_TARGET = 1.5  # 이수성적 조회를 연 뒤 학교가 스스로 목록을 보내는지 기다리는 시간(초)
WAIT_AFTER_QUERY = 3.0  # 조회 버튼을 누른 뒤 응답을 기다리는 시간(초)
PARENT_RETRY = 5.0  # 메뉴를 눌렀는데 이만큼 지나도 다음 메뉴가 안 보이면 (다른 후보를) 다시 눌러 본다
SLOW_FIND_SECONDS = 1.0  # 한 단계에서 요소 찾기가 이보다 오래 걸리면 로그에 남긴다
SCAN_TIMEOUT = 1.0  # 프레임 하나를 한 번에 확인하는 데 기다리는 최대 시간(초)
FULL_SEARCH_EVERY = 5  # 한 번에 확인한 결과를 믿지 않고 모든 프레임을 직접 살피는 주기(단계 수). 놓치는 경우 대비
IDLE_NAV_INTERVAL = 0.5  # 누를 것이 안 보일 때(로딩 중, 로그인 대기) 확인 간격. 학교 화면이 그려질 여유를 준다
MIN_FRAME_INTERVAL = 0.25  # 원격 화면 캡처 최소 간격(초). 그 사이 요청에는 직전 화면을 다시 쓴다
DIAG_SECONDS = 60.0  # 로그인 뒤 이 시간 동안 1초마다 화면 상태를 로그에 남긴다
# 프레임 안에서 찾을 것들이 보이는지 한 번에 확인하는 스크립트. 글자는 앞뒤 공백을 빼고 정확히 같아야 한다.
SCAN_SCRIPT = """(texts) => {
  // 화면 전체 요소를 훑지 않고, 브라우저 기본 기능(XPath)으로 그 글자를 가진 글자 조각만 바로 찾는다.
  const visible = (el) => {
    if (!el || !el.getClientRects().length) return false;
    const style = getComputedStyle(el);
    return style.visibility !== 'hidden' && style.display !== 'none';
  };
  const literal = (s) => s.includes("'") ? 'concat(' + s.split("'").map((p) => "'" + p + "'").join(", \\"'\\", ") + ')' : "'" + s + "'";
  const any = (xpath) => {
    const found = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
    for (let i = 0; i < found.snapshotLength; i++) if (visible(found.snapshotItem(i).parentElement)) return true;
    return false;
  };
  const result = {
    ready: document.readyState,
    chars: document.body ? document.body.textContent.length : 0,
    password: [...document.querySelectorAll('input[type=password]')].some(visible),
    modal: [...document.querySelectorAll('.w2modal_popup')].some(visible),
    target: any("//text()[translate(normalize-space(.), ' ', '') = '이수성적조회']"),
    query: any("//text()[normalize-space(.) = '조회']") || [...document.querySelectorAll('input[type=button],input[type=submit]')].some((el) => el.value.trim() === '조회' && visible(el)),
  };
  for (const t of texts) result['text:' + t] = any('//text()[normalize-space(.) = ' + literal(t) + ']');
  return result;
}"""
# 마우스가 있는 자리의 요소를 보고 학생 화면에 보여 줄 마우스 모양을 정한다.
# 학교 화면의 투명한 팝업 막(w2modal_popup)은 건너뛰고, 같은 사이트의 iframe 안까지 따라 들어간다.
CURSOR_SCRIPT = """(p) => {
  let doc = document, x = p.x, y = p.y;
  for (let depth = 0; depth < 5; depth++) {
    const el = doc.elementsFromPoint(x, y).find((e) => !e.classList.contains('w2modal_popup'));
    if (!el) return 'default';
    if (el.tagName === 'IFRAME' || el.tagName === 'FRAME') {
      try {
        const box = el.getBoundingClientRect();
        if (!el.contentDocument) return 'default';
        doc = el.contentDocument; x -= box.left; y -= box.top;
        continue;
      } catch (e) { return 'default'; }
    }
    const cursor = getComputedStyle(el).cursor;
    if (cursor && cursor !== 'auto' && cursor !== 'default') return cursor;  // 버튼은 기본값이 default 라 아래에서 다시 본다
    if (el.closest('a[href], button, [onclick], [role=button], [role=link], [role=menuitem], [role=tab], label[for], select, summary')) return 'pointer';
    if (el.matches('textarea, [contenteditable=""], [contenteditable=true], input:not([type]), input[type=text], input[type=password], input[type=search], input[type=email], input[type=number], input[type=tel], input[type=url]')) return 'text';
    return 'default';
  }
  return 'default';
}"""
CURSORS = {
    "default", "pointer", "text", "wait", "progress", "help", "move", "not-allowed", "grab", "grabbing",
    "col-resize", "row-resize", "ew-resize", "ns-resize", "crosshair", "copy", "vertical-text",
}
CURSOR_TIMEOUT = 0.5  # 마우스 모양을 확인하는 데 기다리는 최대 시간(초). 넘으면 모양을 바꾸지 않는다
HELP_AFTER_LOGIN = 45.0  # 로그인 뒤 이만큼 지나도 목록을 못 읽으면 학생에게 화면을 다시 보여 준다
RETRY_AFTER_FAILED_CLICK = 1.0  # 메뉴 클릭 자체가 실패했으면 이만큼 뒤에 다시 누른다
SETTLE_AFTER_NAVIGATION = 0.3  # 화면이 바뀐 뒤 다 그려지기를 기다리는 시간(초)
NOTICE_SECONDS = 4.0  # 중요한 안내를 보여 주는 최소 시간
BROWSER_KEEP_SECONDS = 600  # 마지막 연결이 끝나도 Chrome 을 이만큼 켜 두어 다음 시작을 빠르게 한다
REAP_INTERVAL = 15.0


class KnuImportError(Exception):
    """사용자에게 그대로 보여 줄 수 있는 오류."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def _flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name, "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on"}


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
        # 기본으로 켜져 있다. 공개 배포 등에서 끄려면 KNU_IMPORT_ENABLED=0
        enabled=_flag("KNU_IMPORT_ENABLED", default=True),
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
    courses: list[ImportedCourse] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    visited_menus: dict[str, float] = field(default_factory=dict)  # 상위 메뉴를 마지막으로 누른 시각
    target_clicks: int = 0
    query_clicks: int = 0
    wait_until: float = 0.0  # 이 시각까지는 방금 누른 것의 결과를 기다린다
    notice_until: float = 0.0  # 이 시각까지는 중요한 안내를 진행 문구로 덮지 않는다
    last_navigation: float = 0.0  # 마지막으로 화면(페이지)이 바뀐 시각
    nav_task: asyncio.Task | None = None
    last_frame: bytes | None = None
    frame_id: str | None = None
    frame_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    input_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    log_id: int = field(default_factory=lambda: next(_log_ids))  # 로그에서 연결을 구분하는 번호 (토큰 대신)
    last_log: float = field(default_factory=time.monotonic)
    login_seen: bool = False  # 로그인 칸을 본 적이 있는지
    login_done: bool = False  # 로그인 칸이 사라진 것을 확인했는지
    password_visible: bool = False  # 지금 화면에 로그인 칸이 보이는지 (다시 로그인해야 하면 화면을 보여 준다)
    menu_attempts: dict[str, int] = field(default_factory=dict)  # 메뉴별로 눌러 본 횟수 (후보를 돌아가며 고른다)
    fallback_used: bool = False  # 예비 메뉴(학사행정)를 이미 눌렀는지
    # 학교 화면(WebSquare)에는 투명한 팝업 막(w2modal_popup)이 늘 떠 있어 일반 클릭은 1.5초 기다린 뒤 실패한다.
    # 그래서 처음부터 클릭 이벤트를 직접 보낸다. 직접 보내기가 실패하면 일반 클릭을 한 번 시도한다.
    direct_click: bool = True
    pending: dict = field(default_factory=dict)  # 아직 끝나지 않은 요청 → 시작 시각 (진단용)
    find_seconds: float = 0.0  # 이번 단계에서 요소를 찾는 데 쓴 시간 (느리면 로그에 남긴다)
    scan: dict | None = None  # 이번 단계에서 프레임별로 한 번에 확인한 결과
    scan_ms: float = 0.0  # 마지막 한 번에 확인하기에 걸린 시간
    scan_timeouts: int = 0  # 마지막 확인에서 시간 안에 답하지 못한 프레임 수
    steps: int = 0  # 자동 이동 단계 수
    idle: bool = False  # 지난 단계에서 누를 것이 없었는지 (확인 간격을 늘린다)
    login_at: float = 0.0  # 로그인 칸이 사라진 시각
    last_diag: float = 0.0  # 마지막으로 상태 로그를 남긴 시각
    last_capture: float = 0.0  # 마지막으로 화면을 캡처한 시각

    def mark(self, event: str) -> None:
        """단계 하나가 끝났음을 로그에 남긴다. 연결 시작부터와 직전 단계부터의 시간을 함께 적는다."""
        now = time.monotonic()
        log.info("#%d +%.2fs (시작부터 %.2fs) %s", self.log_id, now - self.last_log, now - self.created, event)
        self.last_log = now


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

    async def frame(self, token: str, have: str | None = None) -> dict:
        return await self._worker.run(self._frame(token, have))

    async def send_input(self, token: str, action: KnuInput) -> str | None:
        return await self._worker.run(self._send_input(token, action))

    async def retry_navigation(self, token: str) -> None:
        await self._worker.run(self._retry(token))

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
        context.on("request", lambda request: session.pending.__setitem__(request, time.monotonic()))
        context.on("requestfinished", lambda request: session.pending.pop(request, None))
        context.on("requestfailed", lambda request: session.pending.pop(request, None))
        context.on("page", lambda page: self._on_page(session, cfg, page))
        try:
            page = await context.new_page()
            await self._guard_page(session, cfg, page)
        except Exception as error:
            await self._close(session)
            raise KnuImportError(502, "브라우저 화면을 준비하지 못했습니다. 다시 시도해 주세요.") from error
        session.page = page
        session.mark("원격 브라우저 준비됨")

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
        session.mark("학교 첫 화면 열림 (domcontentloaded)")
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
        session.mark(f"화면 이동: {urlsplit(frame.url).hostname or '(빈 화면)'}")
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
        session.mark(f"이수성적 응답 받음 ({len(courses)}개 과목)")
        session.status = f"이수 과목 {len(courses)}개를 읽었습니다. 아래 목록을 확인해 주세요."
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

    def _pages(self, session: KnuSession) -> list[Any]:
        """열려 있는 모든 창. 지금 보여 주는 창을 먼저 살핀다."""
        if session.context is None:
            return []
        active = self._active_page(session)
        pages = [page for page in session.context.pages if not page.is_closed()]
        return ([active] if active in pages else []) + [page for page in pages if page is not active]

    async def _scan(self, session: KnuSession) -> None:
        """모든 프레임에서 찾을 것들이 보이는지 한 번에 확인해 session.scan 에 둔다.

        요소마다 브라우저에 따로 묻는 대신 프레임마다 스크립트를 한 번만 돌린다. 학교 화면이 무거울 때
        수십 번 주고받던 것을 프레임 수만큼으로 줄인다. 결과는 '이 프레임은 살펴볼 필요가 없다'를
        정하는 데만 쓰고, 실제로 누를 요소는 지금처럼 Playwright 로 찾는다.
        """
        began = time.monotonic()
        frames = [frame for page in self._pages(session) for frame in page.frames]
        texts = [label for label in (*MENU_PATH, FALLBACK_MENU)]

        timeouts = 0

        async def one(frame: Any) -> tuple[Any, dict | None]:
            nonlocal timeouts
            try:
                return frame, await asyncio.wait_for(frame.evaluate(SCAN_SCRIPT, texts), SCAN_TIMEOUT)
            except asyncio.TimeoutError:
                timeouts += 1
                return frame, None
            except Exception:
                return frame, None  # 확인하지 못한 프레임은 예전처럼 직접 살핀다

        session.scan = dict(await asyncio.gather(*(one(frame) for frame in frames)))
        session.scan_ms = (time.monotonic() - began) * 1000
        session.scan_timeouts = timeouts
        session.find_seconds += time.monotonic() - began
        if any(result and result.get("modal") for result in session.scan.values()) and not session.direct_click:
            # 학교의 투명한 팝업 막이 떠 있다. 일반 클릭은 1.5초 기다린 뒤 실패하므로 처음부터 직접 보낸다.
            session.direct_click = True
            session.mark("팝업 막(w2modal_popup) 확인: 클릭 이벤트를 직접 보냅니다")
        self._diagnose(session)
        session.steps += 1
        if session.steps % FULL_SEARCH_EVERY == 0:
            session.scan = None  # 가끔은 결과를 믿지 않고 모든 프레임을 직접 살핀다 (글자가 쪼개져 놓친 경우 대비)

    @staticmethod
    def _diagnose(session: KnuSession) -> None:
        """로그인 뒤 1분 동안, 1초마다 화면 상태를 한 줄 남긴다. 어디서 시간이 가는지 확인하려는 것."""
        now = time.monotonic()
        if not session.login_at or now - session.login_at > DIAG_SECONDS or now - session.last_diag < 1.0:
            return
        session.last_diag = now
        results = [r for r in (session.scan or {}).values() if r]
        seen = sorted({
            key.removeprefix("text:") for r in results for key, value in r.items()
            if value is True and key not in ("ready", "chars")
        })
        pages = ", ".join(f"{r.get('ready')}/{r.get('chars', 0)}자" for r in results) or "확인 못 함"
        pending = ""
        if session.pending:
            request, began = min(session.pending.items(), key=lambda item: item[1])
            parts = urlsplit(getattr(request, "url", ""))
            pending = f", 남은 요청 {len(session.pending)}개 (가장 오래된 것 {now - began:.1f}s: {parts.hostname}{parts.path[:60]})"
        session.mark(
            f"상태: 프레임 {len(session.scan or {})}개, 확인 {session.scan_ms:.0f}ms"
            f"{f' (시간 초과 {session.scan_timeouts}개)' if session.scan_timeouts else ''}, 화면 {pages}"
            f"{pending or ', 남은 요청 없음'}, 보이는 것: {', '.join(seen) or '없음'}"
        )

    @staticmethod
    def _worth_looking(session: KnuSession, frame: Any, key: str | None) -> bool:
        if key is None or session.scan is None:
            return True
        result = session.scan.get(frame)
        return result is None or bool(result.get(key))

    async def _find(self, session: KnuSession, locate: Callable[[Any], Any], key: str | None = None) -> tuple[Any, Any]:
        """모든 창의 모든 프레임에서 처음 보이는 요소를 찾는다. (창, 요소) 또는 (None, None)."""
        found = await self._find_all(session, locate, limit=1, key=key)
        return found[0] if found else (None, None)

    async def _find_all(
        self, session: KnuSession, locate: Callable[[Any], Any], limit: int = 10, key: str | None = None
    ) -> list[tuple[Any, Any]]:
        """모든 창·프레임에서 보이는 요소를 최대 limit 개 찾는다. [(창, 요소), ...]

        key 를 주면 한 번에 확인한 결과(session.scan)에서 그것이 없다고 나온 프레임은 건너뛴다.
        """
        began = time.monotonic()
        try:
            return await self._collect(session, locate, limit, key)
        finally:
            session.find_seconds += time.monotonic() - began

    async def _collect(self, session: KnuSession, locate: Callable[[Any], Any], limit: int, key: str | None) -> list[tuple[Any, Any]]:
        found: list[tuple[Any, Any]] = []
        for page in self._pages(session):
            for frame in page.frames:
                if not self._worth_looking(session, frame, key):
                    continue
                try:
                    items = locate(frame)
                    for index in range(min(await items.count(), limit)):
                        candidate = items.nth(index)
                        if await candidate.is_visible():
                            found.append((page, candidate))
                            if len(found) >= limit:
                                return found
                except Exception:
                    continue
        return found

    @staticmethod
    def _reason(error: Exception) -> str:
        """Playwright 오류에서 원인 한 줄을 뽑는다 (예: 다른 요소가 클릭을 가로챔). 로그용, 200자까지."""
        lines = [line.strip(" -") for line in str(error).splitlines() if line.strip(" -")]
        if not lines:
            return type(error).__name__
        keywords = ("intercepts pointer events", "not stable", "not visible", "outside of the viewport", "not enabled", "detached")
        detail = next((line for line in reversed(lines) if any(k in line for k in keywords)), lines[-1])
        return f"{type(error).__name__}: {detail}"[:200]

    @staticmethod
    def _query_button(frame: Any) -> Any:
        return frame.get_by_role("button", name=QUERY_TEXT).or_(frame.get_by_text(QUERY_TEXT))

    async def _click(self, session: KnuSession, page: Any, element: Any, status: str, wait: float) -> None:
        if session.finished or session.closed:
            return  # 요소를 찾는 사이 목록을 받았다. 더 누르지 않는다
        session.page = page  # 자동으로 누른 창을 보여 줘서 학생이 진행 상황을 볼 수 있게 한다
        session.status = status
        session.wait_until = time.monotonic() + wait
        if session.direct_click:
            try:
                await element.dispatch_event("click", timeout=1500)
                session.mark(f"클릭 이벤트를 직접 보냄: {status}")
                return
            except Exception as error:
                session.mark(f"클릭 이벤트 실패 ({self._reason(error)}), 일반 클릭 시도: {status}")
            try:
                await element.click(timeout=1500)
            except Exception as error:
                session.wait_until = 0.0  # 누르지 못했으니 결과를 기다릴 필요가 없다
                session.mark(f"일반 클릭도 실패 ({self._reason(error)}): {status}")
                raise
            session.mark(f"자동 클릭: {status}")
            return
        try:
            await element.click(timeout=1500)
            session.mark(f"자동 클릭: {status}")
            return
        except Exception as error:
            reason = self._reason(error)
            session.mark(f"자동 클릭 실패 ({reason}): {status}")
            if "intercepts pointer events" in reason:
                session.direct_click = True
        # 다른 요소에 가려졌거나 움직이는 중이면, 그 요소에 클릭 이벤트를 직접 보낸다 (메뉴 동작은 같다).
        try:
            await element.dispatch_event("click", timeout=1500)
        except Exception as error:
            session.wait_until = 0.0  # 누르지 못했으니 결과를 기다릴 필요가 없다
            session.mark(f"클릭 이벤트도 실패 ({self._reason(error)}): {status}")
            raise
        session.mark(f"클릭 이벤트를 직접 보냄: {status}")

    async def _navigate_step(self, session: KnuSession) -> bool:
        """메뉴를 한 단계 누른다. 자동 이동을 그만둬야 하면 True."""
        if session.finished or session.closed:
            return True  # 이미 목록을 받았으면 더 누르지 않는다
        now = time.monotonic()
        if now < session.wait_until:
            return False  # 방금 누른 것의 결과를 기다린다
        if now - session.last_navigation < SETTLE_AFTER_NAVIGATION:
            return False  # 화면이 막 바뀌어 아직 그리는 중일 수 있다 (로그인 칸이 늦게 나타나는 경우)

        # 비밀번호 칸이 보이면 아직 로그인 전이다. 로그인 화면의 메뉴를 미리 누르지 않는다.
        await self._scan(session)
        session.idle = False
        page, _ = await self._find(session, lambda frame: frame.locator("input[type=password]"), key="password")
        session.password_visible = page is not None
        if page is not None:
            session.idle = True  # 학생이 로그인하는 중이다
            if not session.login_seen:
                session.login_seen = True
                session.mark("로그인 칸 보임")
            if not session.target_clicks:
                self._info(session, "학교 화면에서 로그인해 주세요. 로그인하면 이수성적 조회까지 자동으로 이동합니다.")
            return False

        if session.login_seen and not session.login_done:
            session.login_done = True
            session.login_at = time.monotonic()
            session.mark("로그인 칸 사라짐 (로그인 완료로 판단)")

        # 이수성적 조회 화면을 열었는데 응답이 없으면 '조회' 버튼을 누른다.
        if session.target_clicks and session.query_clicks < QUERY_CLICK_LIMIT:
            page, button = await self._find(session, self._query_button, key="query")
            if button is not None:
                session.query_clicks += 1
                await self._click(session, page, button, "조회 버튼을 눌러 이수 과목을 불러오는 중입니다.", WAIT_AFTER_QUERY)
                return False

        page, target = await self._find(session, lambda frame: frame.get_by_text(TARGET_TEXT), key="target")
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

        # 경로의 가장 깊은 단계부터 찾는다. '학기성적'이 보이면 '성적'을 다시 누르지 않는다 (메뉴가 접힐 수 있다).
        for label in reversed(MENU_PATH):
            found = await self._find_all(
                session, lambda frame, label=label: frame.get_by_text(label, exact=True), key=f"text:{label}"
            )
            if not found:
                continue
            if now - session.visited_menus.get(label, float("-inf")) < PARENT_RETRY:
                return False  # 방금 누른 메뉴다. 다음 메뉴가 펼쳐지기를 기다린다
            attempt = session.menu_attempts.get(label, 0)
            if label == MENU_PATH[0] and attempt >= FALLBACK_AFTER and not session.fallback_used:
                # '성적'이 여러 번 안 펼쳐졌다. 예비로 학사행정을 한 번 열고, 곧 '성적'을 다시 누른다.
                session.fallback_used = True
                page, menu = await self._find(
                    session, lambda frame: frame.get_by_text(FALLBACK_MENU, exact=True), key=f"text:{FALLBACK_MENU}"
                )
                if menu is not None:
                    session.visited_menus[label] = now - PARENT_RETRY + RETRY_AFTER_FAILED_CLICK
                    try:
                        await self._click(session, page, menu, f"'{FALLBACK_MENU}' 메뉴를 먼저 열어 봅니다.", WAIT_AFTER_MENU)
                    except Exception:
                        pass
                    return False
            # 같은 글자가 여러 개면 시도할 때마다 다음 후보를 누른다 (첫 번째가 다른 곳의 '성적'일 수 있다).
            session.menu_attempts[label] = attempt + 1
            page, menu = found[attempt % len(found)]
            session.visited_menus[label] = now
            try:
                await self._click(session, page, menu, f"'{label}' 메뉴에서 이수성적 조회를 찾고 있습니다.", WAIT_AFTER_MENU)
            except Exception:
                # 화면이 덜 그려져 누르지 못했으면 15초를 기다리지 않고 곧 다시 누른다.
                session.visited_menus[label] = now - PARENT_RETRY + RETRY_AFTER_FAILED_CLICK
            return False

        if not session.target_clicks:
            self._info(session, "이수성적 조회 메뉴를 찾고 있습니다. 화면에 보이면 직접 눌러도 됩니다.")
        session.idle = True  # 누를 것이 없다 (화면이 아직 그려지는 중일 수 있다)
        return False

    @staticmethod
    def _info(session: KnuSession, text: str) -> None:
        """기다리는 중이라는 문구. 막 보여 준 중요한 안내(학교 밖 이동 등)는 덮지 않는다."""
        if time.monotonic() >= session.notice_until:
            session.status = text

    async def _auto_navigate(self, session: KnuSession) -> None:
        # 메뉴가 보이지 않는 동안(로그인, 추가 인증 중)에는 기다리기만 한다.
        # 오래 걸려도 연결은 미사용 시간과 최대 사용 시간으로 정리된다.
        while not session.closed and not session.finished:
            await asyncio.sleep(IDLE_NAV_INTERVAL if session.idle else NAV_INTERVAL)
            if session.closed or session.finished:
                return  # 기다리는 사이 목록을 받았다
            if time.monotonic() - session.last_typing < NAV_PAUSE_AFTER_TYPING:
                continue  # 학생이 글자를 치는 중에는 화면을 건드리지 않는다
            session.find_seconds = 0.0
            try:
                if await self._navigate_step(session):
                    return
            except Exception:
                session.status = "자동 이동을 시도하고 있습니다. 메뉴가 보이지 않으면 화면에서 직접 선택해 주세요."
            if session.find_seconds > SLOW_FIND_SECONDS:
                session.mark(f"화면에서 메뉴를 찾는 데 {session.find_seconds:.2f}s 걸림")

    async def _retry(self, token: str) -> None:
        session = self._get(token)
        session.last_seen = time.monotonic()
        if session.finished:
            return
        session.visited_menus.clear()
        session.menu_attempts.clear()
        session.fallback_used = False
        session.target_clicks = session.query_clicks = 0
        session.wait_until = 0.0
        session.status = "자동 이동을 다시 시도합니다."
        if session.nav_task is None or session.nav_task.done():
            session.nav_task = asyncio.create_task(self._auto_navigate(session))

    async def _frame(self, token: str, have: str | None = None) -> dict:
        session = self._get(token)
        session.last_seen = time.monotonic()
        page = self._active_page(session)
        fresh = time.monotonic() - session.last_capture < MIN_FRAME_INTERVAL
        if page is not None and not fresh and not session.frame_lock.locked():
            async with session.frame_lock:
                try:
                    session.last_capture = time.monotonic()
                    session.last_frame = await page.screenshot(
                        type="jpeg", quality=55, timeout=5000, caret="initial"  # 입력칸의 깜빡이는 커서도 보여 준다
                    )
                    session.frame_id = hashlib.blake2b(session.last_frame, digest_size=8).hexdigest()
                except Exception:
                    pass  # 이번 캡처를 건너뛰고 직전 화면을 보여 준다
        cfg = settings()
        now = time.monotonic()
        expires = min(cfg.idle_seconds, cfg.max_seconds - (now - session.created))
        return {
            # 학생 화면에 이미 있는 것과 같으면 이미지를 다시 보내지 않는다.
            "image": base64.b64encode(session.last_frame).decode()
            if session.last_frame and session.frame_id != have
            else None,
            "frame_id": session.frame_id,
            "status": session.status,
            "finished": session.finished,
            "courses": session.courses,
            "duplicates": session.duplicates,
            "expires_in": max(0, int(expires)),
            # 로그인을 마치면 학생 화면에서는 학교 화면을 가리고 진행 상황만 보여 준다.
            "logged_in": session.login_done and not session.password_visible,
            "needs_help": session.login_done
            and not session.finished
            and now - session.login_at > HELP_AFTER_LOGIN,
        }

    async def _send_input(self, token: str, action: KnuInput) -> str | None:
        """입력을 보낸다. 마우스 이동이면 그 자리의 마우스 모양(예: pointer, text)을 돌려준다."""
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
            elif action.type == "move" and action.x is not None and action.y is not None:
                await page.mouse.move(action.x, action.y)  # 학교 화면의 메뉴 강조 같은 효과도 보이게 된다
                return await self._cursor_at(page, action.x, action.y)
            else:
                raise KnuImportError(400, "보낼 수 없는 입력입니다.")
        return None

    @staticmethod
    async def _cursor_at(page: Any, x: float, y: float) -> str | None:
        try:
            cursor = await asyncio.wait_for(page.evaluate(CURSOR_SCRIPT, {"x": x, "y": y}), CURSOR_TIMEOUT)
        except Exception:
            return None  # 화면이 바쁘면 지금 모양을 그대로 둔다
        return cursor if cursor in CURSORS else "default"

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
