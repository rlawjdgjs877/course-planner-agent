"""경북대 이수 과목 불러오기 (실험 기능): 실제 브라우저와 학교 계정 없이 확인할 수 있는 부분."""

import base64
import logging
import time
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import knu_session
from app.services.knu_session import KnuSessionManager
from app.services.knu_transcript import extract_courses

LOCAL = ("127.0.0.1", 50000)


# ---------- 응답에서 과목 뽑기 ----------


def test_extract_courses_drops_f_and_np_and_keeps_only_four_fields():
    payload = {
        "data": [
            {"sbjetCd": "COMP0201", "sbjetNm": "자료구조", "crdit": "3", "sbjetSctnm": "전공필수", "gradsGradCd": "A+", "gradsPnt": 4.5},
            {"sbjetCd": "COMP0202", "sbjetNm": "이산수학", "crdit": 3, "sbjetSctnm": "전공기반", "gradsGradCd": "F"},
            {"sbjetCd": "CLTR0001", "sbjetNm": "봉사활동", "crdit": 1, "sbjetSctnm": "교양", "gradsGradCd": "NP"},
            {"sbjetCd": "CLTR0002", "sbjetNm": "글쓰기", "crdit": "2.0", "sbjetSctnm": "교양", "gradsGradCd": "P"},
        ]
    }
    courses, duplicates = extract_courses(payload)
    assert [c.model_dump() for c in courses] == [
        {"code": "COMP0201", "name": "자료구조", "credits": 3.0, "category": "전공필수"},
        {"code": "CLTR0002", "name": "글쓰기", "credits": 2.0, "category": "교양"},
    ]
    assert duplicates == []


def test_extract_courses_reports_repeated_codes_and_skips_broken_rows():
    payload = {
        "data": [
            {"sbjetCd": "COMP0201", "sbjetNm": "자료구조", "crdit": 3, "gradsGradCd": "C0"},
            {"sbjetCd": "COMP0201", "sbjetNm": "자료구조", "crdit": 3, "gradsGradCd": "A0"},
            {"sbjetCd": "", "sbjetNm": "이름만", "crdit": 3},
            "not a row",
            {"sbjetCd": "COMP0300", "sbjetNm": "운영체제", "crdit": "?", "sbjetSctnm": ""},
        ]
    }
    courses, duplicates = extract_courses(payload)
    assert [c.code for c in courses] == ["COMP0201", "COMP0300"]
    assert courses[1].credits is None and courses[1].category is None
    assert duplicates == ["COMP0201"]


@pytest.mark.parametrize("payload", [None, [], {"data": None}, {"result": []}])
def test_extract_courses_rejects_unexpected_shapes(payload):
    with pytest.raises(ValueError):
        extract_courses(payload)


# ---------- 가짜 브라우저 ----------


class FakePage:
    def __init__(self, context):
        self.context, self.closed, self.frames, self.actions = context, False, [], []
        self.mouse = SimpleNamespace(click=self._click, wheel=self._wheel)
        self.keyboard = SimpleNamespace(press=self._press, insert_text=self._text)
        self.main_frame, self.handlers, self.went_back = SimpleNamespace(url="about:blank"), {}, 0

    def on(self, event, handler):
        self.handlers[event] = handler

    async def goto(self, url, **_):
        if self.context.browser.fail_goto:
            raise RuntimeError("network down")

    async def go_back(self):
        self.went_back += 1

    async def close(self):
        self.closed = True

    def navigate(self, url):
        """화면이 url 로 바뀐 것처럼 framenavigated 를 보낸다."""
        self.main_frame.url = url
        self.handlers["framenavigated"](self.main_frame)

    def is_closed(self):
        return self.closed

    async def screenshot(self, **_):
        return b"\xff\xd8fake-jpeg"

    async def _click(self, x, y):
        self.actions.append(("click", x, y))

    async def _wheel(self, dx, dy):
        self.actions.append(("scroll", dy))

    async def _press(self, key):
        self.actions.append(("key", key))

    async def _text(self, text):
        self.actions.append(("text", text))


class FakeContext:
    def __init__(self, browser):
        self.browser, self.handlers, self.pages, self.closed, self.route_handler = browser, {}, [], False, None

    def on(self, event, handler):
        self.handlers[event] = handler

    async def route(self, _pattern, handler):
        self.route_handler = handler

    async def new_page(self):
        page = FakePage(self)
        self.pages.append(page)
        return page

    async def close(self):
        self.closed = True


class FakeBrowser:
    def __init__(self):
        self.contexts, self.fail_goto, self.closed = [], False, False

    async def new_context(self, **options):
        assert options["accept_downloads"] is False
        context = FakeContext(self)
        self.contexts.append(context)
        return context


@pytest.fixture
def fake(monkeypatch):
    browser = FakeBrowser()

    async def factory(_cfg):
        browser.closed = False

        async def close():
            browser.closed = True

        return close, browser

    manager = KnuSessionManager(browser_factory=factory)
    monkeypatch.setattr(knu_session, "manager", manager)
    monkeypatch.setenv("KNU_IMPORT_ENABLED", "1")
    for name in ("KNU_IMPORT_ALLOW_REMOTE", "KNU_IMPORT_IDLE_SECONDS", "KNU_IMPORT_MAX_SESSIONS"):
        monkeypatch.delenv(name, raising=False)
    yield SimpleNamespace(manager=manager, browser=browser, client=TestClient(app, client=LOCAL))
    manager.shutdown()


def start(client, consent=True):
    return client.post("/import/knu/start", json={"consent": consent})


def header(token):
    return {"X-Import-Session": token}


def run(manager, coroutine):
    return manager._worker.run_blocking(coroutine, timeout=5)


def respond(fake, context, url, payload):
    response = SimpleNamespace(url=url)

    async def body():
        return payload

    response.json = body
    run(fake.manager, context.handlers["response"](response))


# ---------- 켜짐/꺼짐과 접근 제한 ----------


def test_feature_is_off_by_default(monkeypatch):
    monkeypatch.delenv("KNU_IMPORT_ENABLED", raising=False)
    client = TestClient(app, client=LOCAL)
    status = client.get("/import/knu/status").json()
    assert status["enabled"] is False and status["available"] is False
    assert "꺼져" in status["reason"]
    assert start(client).status_code == 503


def test_only_this_computer_unless_allowed(fake, monkeypatch):
    remote = TestClient(app, client=("10.0.0.7", 40000))
    assert remote.get("/import/knu/status").json()["available"] is False
    assert start(remote).status_code == 403

    monkeypatch.setenv("KNU_IMPORT_ALLOW_REMOTE", "1")
    assert start(remote).status_code == 200


def test_consent_is_required(fake):
    response = start(fake.client, consent=False)
    assert response.status_code == 400
    assert fake.browser.contexts == []


def test_other_sites_cannot_drive_the_api(fake):
    response = fake.client.post(
        "/import/knu/start", json={"consent": True}, headers={"Origin": "https://evil.example"}
    )
    assert response.status_code == 403
    same = fake.client.post("/import/knu/start", json={"consent": True}, headers={"Origin": "http://testserver"})
    assert same.status_code == 200


# ---------- 세션 ----------


def test_each_student_gets_a_separate_session(fake):
    first, second = start(fake.client).json()["session"], start(fake.client).json()["session"]
    assert first != second and len(first) >= 40
    context_a, context_b = fake.browser.contexts

    respond(fake, context_a, "https://knuin.knu.ac.kr/x/searchTotalGradsInqrList.knu",
            {"data": [{"sbjetCd": "COMP0201", "sbjetNm": "자료구조", "crdit": 3, "sbjetSctnm": "전공필수", "gradsGradCd": "B+"}]})
    respond(fake, context_a, "https://knuin.knu.ac.kr/other/list", {"data": [{"sbjetCd": "X", "sbjetNm": "무시"}]})

    frame_a = fake.client.post("/import/knu/frame", headers=header(first)).json()
    frame_b = fake.client.post("/import/knu/frame", headers=header(second)).json()
    assert frame_a["finished"] is True
    assert [c["code"] for c in frame_a["courses"]] == ["COMP0201"]
    assert frame_b["finished"] is False and frame_b["courses"] == []
    # 과목을 다 읽으면 그 학생의 브라우저(학교 세션)는 바로 닫고, 다른 학생은 그대로 둔다.
    assert context_a.closed and not context_b.closed
    assert frame_a["image"] is None
    assert base64.b64decode(frame_b["image"]).startswith(b"\xff\xd8")
    # 화면을 숨긴 채 상태만 물으면 캡처하지 않는다.
    assert fake.client.post("/import/knu/frame", json={"image": False}, headers=header(second)).json()["image"] is None


def test_unknown_or_missing_token_is_rejected(fake):
    start(fake.client)
    assert fake.client.post("/import/knu/frame").status_code == 404
    assert fake.client.post("/import/knu/frame", headers=header("guess")).status_code == 404
    assert fake.client.post("/import/knu/input", json={"type": "text", "text": "a"}).status_code == 404


def test_inputs_are_relayed_and_limited(fake):
    token = start(fake.client).json()["session"]
    page = fake.browser.contexts[0].pages[0]
    send = lambda body: fake.client.post("/import/knu/input", json=body, headers=header(token))

    assert send({"type": "click", "x": 100, "y": 200}).status_code == 200
    assert send({"type": "text", "text": "한글"}).status_code == 200
    assert send({"type": "key", "key": "Enter"}).status_code == 200
    assert send({"type": "scroll", "delta": 300}).status_code == 200
    assert page.actions == [("click", 100, 200), ("text", "한글"), ("key", "Enter"), ("scroll", 300)]

    assert send({"type": "key", "key": "Control+A"}).status_code == 400
    assert send({"type": "click", "x": 5000, "y": 10}).status_code == 422
    assert send({"type": "text", "text": "x" * 201}).status_code == 422


def test_stop_closes_the_browser_context_and_forgets_results(fake):
    token = start(fake.client).json()["session"]
    context = fake.browser.contexts[0]
    respond(fake, context, "https://knuin.knu.ac.kr/searchTotalGradsInqrList",
            {"data": [{"sbjetCd": "A1", "sbjetNm": "과목", "crdit": 3}]})

    assert fake.client.post("/import/knu/stop", headers=header(token)).json()["closed"] is True
    assert context.closed is True
    assert fake.manager.session_count() == 0
    assert fake.client.post("/import/knu/frame", headers=header(token)).status_code == 404

    # 다음 시작을 빠르게 하려고 Chrome 은 잠시 켜 두었다가, 오래 쓰지 않으면 닫는다.
    assert fake.browser.closed is False
    fake.manager._idle_since -= knu_session.BROWSER_KEEP_SECONDS + 1
    run(fake.manager, fake.manager._reap(knu_session.settings()))
    assert fake.browser.closed is True


def test_browser_is_prepared_while_the_student_reads(fake):
    assert fake.client.get("/import/knu/status").json()["available"] is True
    assert wait_for(lambda: fake.manager._browser is not None)
    start(fake.client)
    assert len(fake.browser.contexts) == 1  # 미리 띄운 Chrome 을 그대로 쓴다


def test_warm_browser_is_reused(fake):
    first = start(fake.client).json()["session"]
    fake.client.post("/import/knu/stop", headers=header(first))
    start(fake.client)
    assert len(fake.browser.contexts) == 2 and fake.browser.closed is False  # 같은 Chrome 에 새 창만 만든다


def test_stop_from_page_close_uses_the_body(fake):
    token = start(fake.client).json()["session"]
    assert fake.client.post("/import/knu/stop", json={"session": token}).json()["closed"] is True
    assert fake.browser.contexts[0].closed is True


def test_idle_sessions_are_cleaned_up(fake, monkeypatch):
    token = start(fake.client).json()["session"]
    session = fake.manager._sessions[token]
    session.last_seen -= 3600
    run(fake.manager, fake.manager._reap(knu_session.settings()))
    assert fake.browser.contexts[0].closed is True
    assert fake.client.post("/import/knu/frame", headers=header(token)).status_code == 404


def test_session_limit(fake, monkeypatch):
    monkeypatch.setenv("KNU_IMPORT_MAX_SESSIONS", "2")
    assert start(fake.client).status_code == 200
    assert start(fake.client).status_code == 200
    assert start(fake.client).status_code == 429


def navigate(fake, page, url):
    """원격 창의 화면이 url 로 바뀐 것처럼 알린다 (실제처럼 브라우저 전용 스레드에서)."""

    async def go():
        page.navigate(url)

    run(fake.manager, go())


def open_popup(fake, session, popup):
    async def go():
        fake.manager._on_page(session, knu_session.settings(), popup)

    run(fake.manager, go())


def wait_for(predicate, seconds=3.0):
    deadline = time.time() + seconds
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.05)
    return False


def test_school_page_failure_is_shown_and_cleaned_up_on_stop(fake):
    fake.browser.fail_goto = True
    token = start(fake.client).json()["session"]  # 학교 페이지를 다 열기 전에 돌려준다
    status = lambda: fake.client.post("/import/knu/frame", headers=header(token)).json()["status"]
    assert wait_for(lambda: "열지 못했습니다" in status())
    fake.client.post("/import/knu/stop", headers=header(token))
    assert fake.manager.session_count() == 0
    assert fake.browser.contexts[0].closed is True


def test_unchanged_screen_is_not_sent_again(fake):
    token = start(fake.client).json()["session"]
    first = fake.client.post("/import/knu/frame", headers=header(token)).json()
    assert first["image"] and first["frame_id"]
    again = fake.client.post("/import/knu/frame", json={"have": first["frame_id"]}, headers=header(token)).json()
    assert again["image"] is None and again["frame_id"] == first["frame_id"]
    other = fake.client.post("/import/knu/frame", json={"have": "old"}, headers=header(token)).json()
    assert other["image"] == first["image"]


def test_leaving_the_school_is_undone(fake):
    token = start(fake.client).json()["session"]
    context = fake.browser.contexts[0]
    main = context.pages[0]

    for url in ["https://knuin.knu.ac.kr/webview/main/Main.knu", "https://sso.knu.ac.kr/login", "about:blank"]:
        navigate(fake, main, url)
    assert main.went_back == 0

    for url in ["https://evil.example/phish", "https://knu.ac.kr.evil.example/"]:
        navigate(fake, main, url)
    assert wait_for(lambda: main.went_back == 2)  # 원래 창은 이전 화면으로 되돌린다
    status = fake.client.post("/import/knu/frame", headers=header(token)).json()["status"]
    assert "되돌렸습니다" in status

    # 새 창이 밖의 주소로 열리면 그 창을 닫는다.
    popup = FakePage(context)
    context.pages.append(popup)
    open_popup(fake, fake.manager._sessions[token], popup)
    assert wait_for(lambda: "framenavigated" in popup.handlers)
    navigate(fake, popup, "https://ads.example.com/")
    assert wait_for(lambda: popup.closed)


def test_typed_text_never_reaches_the_logs(fake, caplog):
    caplog.set_level(logging.DEBUG)
    token = start(fake.client).json()["session"]
    secret = "pw-Secret-9137"
    fake.client.post("/import/knu/input", json={"type": "text", "text": secret}, headers=header(token))
    fake.client.post("/import/knu/input", json={"type": "text", "text": secret}, headers=header("bad-token"))
    fake.client.post("/import/knu/stop", headers=header(token))
    assert secret not in caplog.text
    assert token not in caplog.text


class FakeLocator:
    def __init__(self, found, clicks=None, name=""):
        self.found, self.clicks, self.name = found, clicks if clicks is not None else [], name

    async def count(self):
        return 1 if self.found else 0

    def nth(self, _index):
        return self

    async def is_visible(self):
        return self.found

    async def click(self, timeout):
        self.clicks.append(self.name)

    def or_(self, other):
        return self if self.found else other


class FakeFrame:
    """보이는 글자 목록과 비밀번호 칸 여부만 흉내 낸다. 누른 글자를 clicks 에 남긴다."""

    def __init__(self, labels, password=False):
        self.labels, self.password, self.clicks = list(labels), password, []

    def _match(self, text, exact=False):
        for label in self.labels:
            if (text.match(label) if hasattr(text, "match") else label == text):
                return FakeLocator(True, self.clicks, label)
        return FakeLocator(False)

    def get_by_text(self, text, exact=False):
        return self._match(text, exact)

    def get_by_role(self, role, name=None):
        return self._match(name) if role == "button" else FakeLocator(False)

    def locator(self, selector):
        return FakeLocator(self.password and "password" in selector)


def step(fake, session):
    return run(fake.manager, fake.manager._navigate_step(session))


def test_auto_navigation_waits_for_login_and_menus(fake):
    token = start(fake.client).json()["session"]
    session = fake.manager._sessions[token]
    page = fake.browser.contexts[0].pages[0]

    # 비밀번호 칸이 보이면 메뉴가 보여도 누르지 않는다 (로그인 전).
    page.frames = [FakeFrame(["학사행정", "이수성적 조회"], password=True)]
    for _ in range(5):
        assert step(fake, session) is False
    assert page.frames[0].clicks == []
    assert "로그인" in session.status

    # 로그인했지만 메뉴가 없으면 몇 번을 시도해도 멈추지 않는다.
    page.frames = [FakeFrame([])]
    for _ in range(200):
        assert step(fake, session) is False


def test_auto_navigation_presses_query_button_then_gives_up(fake):
    token = start(fake.client).json()["session"]
    session = fake.manager._sessions[token]
    frame = FakeFrame(["이수 성적 조회", "조회"])
    fake.browser.contexts[0].pages[0].frames = [frame]
    wait = lambda: setattr(session, "wait_until", 0)  # 응답을 기다린 시간이 지난 것처럼

    assert step(fake, session) is False and frame.clicks == ["이수 성적 조회"]
    assert step(fake, session) is False and len(frame.clicks) == 1  # 열고 나서 잠시 기다린다
    for expected in ["조회", "조회", "이수 성적 조회", "조회", "조회", "이수 성적 조회", "조회", "조회"]:
        wait()
        assert step(fake, session) is False
        assert frame.clicks[-1] == expected
    wait()
    assert step(fake, session) is True  # 메뉴 3번, 조회 버튼 6번을 눌러도 응답이 없으면 멈춘다
    assert "멈췄습니다" in session.status

    # '자동 이동 다시 시도'를 누르면 처음부터 다시 센다.
    assert fake.client.post("/import/knu/navigate", headers=header(token)).status_code == 200
    assert session.target_clicks == session.query_clicks == 0
    assert step(fake, session) is False and frame.clicks[-1] == "이수 성적 조회"


def test_auto_navigation_looks_in_every_window_and_retries_parent_menus(fake):
    token = start(fake.client).json()["session"]
    session = fake.manager._sessions[token]
    context = fake.browser.contexts[0]
    main = context.pages[0]
    main.frames = [FakeFrame(["학사행정"])]

    # 공지 팝업이 떠서 그 창을 보여 주고 있어도, 원래 창의 메뉴를 찾는다.
    popup = FakePage(context)
    popup.frames = [FakeFrame(["닫기"])]
    context.pages.append(popup)
    open_popup(fake, session, popup)
    assert step(fake, session) is False
    assert main.frames[0].clicks == ["학사행정"]
    assert session.page is main  # 누른 창을 보여 준다

    # 상위 메뉴는 바로 다시 누르지 않지만, 시간이 지나도 못 찾으면 다시 눌러 본다.
    assert step(fake, session) is False and len(main.frames[0].clicks) == 1
    session.visited_menus["학사행정"] -= 60
    session.wait_until = 0  # 방금 누른 메뉴의 결과를 기다리는 시간도 지난 것처럼
    assert step(fake, session) is False and len(main.frames[0].clicks) == 2
