"""경북대 이수 과목 불러오기를 진짜 Chrome 으로 확인한다. 학교 대신 이 컴퓨터에 띄운 가짜 학교 페이지를 쓴다.

실제 학교 화면과 메뉴 구조, 로그인 방식은 다를 수 있다. 여기서는 우리 코드의 흐름
(원격 입력, 자동 메뉴 이동, 응답 읽기, 주소 제한, 세션 분리, 정리)만 확인한다.
Playwright 나 Chrome 이 없으면 건너뛴다.
"""

import base64
import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import knu_session
from app.services.knu_session import KnuSessionManager

pytestmark = pytest.mark.skipif(not knu_session.playwright_installed(), reason="Playwright 가 설치되어 있지 않음")

# 실제 학교에서 생길 수 있는 세 가지를 넣었다.
# 1) 로그인 전에도 '성적' 메뉴가 보인다. 미리 눌러도 로그인하면 메뉴가 닫힌 상태로 다시 그려진다.
#    메뉴는 성적 → 학기성적 → 이수성적 조회 순서로 펼쳐지고, 누르면 안 되는 '학사행정'도 함께 보인다.
# 2) 로그인하면 공지 팝업 창이 뜬다.
# 3) 이수성적 조회 화면은 '조회' 버튼을 눌러야 목록을 보낸다.
# 4) 로그인 직후 투명한 막이 '성적' 메뉴를 덮어 일반 클릭이 막힌다.
MOCK_PAGE = """<!doctype html><html lang="ko"><meta charset="utf-8"><title>가짜 학사시스템</title>
<style>body{font:16px sans-serif;margin:40px} input,button{font-size:18px;margin:6px;padding:6px}</style>
<nav id="menu">
  <a href="#" onclick="window.wrongMenu=true;return false">학사행정</a>
  <span style="position:relative;display:inline-block"><a href="#" onclick="document.getElementById('sub').hidden=false;return false">성적</a><span id="cover" hidden style="position:absolute;inset:0;background:transparent"></span></span>
  <div id="sub" hidden><a href="#" onclick="document.getElementById('sub2').hidden=false;return false">학기성적</a></div>
  <div id="sub2" hidden><a href="#" onclick="openGrades();return false">이수성적 조회</a></div>
</nav>
<div id="login">
  <input id="uid" aria-label="아이디"><input id="pwd" type="password" aria-label="비밀번호">
  <button id="login-btn" onclick="login()">로그인</button>
</div>
<div id="grades" hidden><h2>이수성적 조회</h2><button id="query" onclick="loadGrades()">조회</button></div>
<p id="result"></p>
<script>
function show(){
  document.getElementById('login').hidden=true;
  document.getElementById('sub').hidden=true;  // 로그인하면 메뉴가 닫힌 상태로 다시 그려진다
  document.getElementById('sub2').hidden=true;
  document.getElementById('cover').hidden=false;  // 로그인 직후 투명한 막이 '성적' 메뉴를 덮는다
}
function login(){
  if(document.getElementById('uid').value==='student' && document.getElementById('pwd').value){
    document.cookie='mock_session=1; path=/'; show();
    window.open('/notice', 'notice', 'width=420,height=300');
  }
}
if(document.cookie.includes('mock_session=1')) show();
function openGrades(){ document.getElementById('grades').hidden=false; }
async function loadGrades(){
  const r = await fetch('/api/grade/searchTotalGradsInqrList.knu', {method:'POST'});
  const d = await r.json();
  document.getElementById('result').textContent = d.data.length + '건 조회';
}
</script></html>"""

NOTICE_PAGE = """<!doctype html><html lang="ko"><meta charset="utf-8"><title>공지</title>
<p>학사 공지입니다.</p><button onclick="window.close()">닫기</button></html>"""

MOCK_GRADES = {
    "data": [
        {"sbjetCd": "COMP0201", "sbjetNm": "자료구조", "crdit": "3", "sbjetSctnm": "전공필수", "gradsGradCd": "A+"},
        {"sbjetCd": "COMP0202", "sbjetNm": "이산수학", "crdit": "3", "sbjetSctnm": "전공기반", "gradsGradCd": "F"},
        {"sbjetCd": "CLTR0010", "sbjetNm": "봉사", "crdit": "1", "sbjetSctnm": "교양", "gradsGradCd": "NP"},
        {"sbjetCd": "CLTR0001", "sbjetNm": "글쓰기", "crdit": "2", "sbjetSctnm": "교양", "gradsGradCd": "B0"},
        {"sbjetCd": "COMP0201", "sbjetNm": "자료구조", "crdit": "3", "sbjetSctnm": "전공필수", "gradsGradCd": "C+"},
    ]
}


class MockSchool(BaseHTTPRequestHandler):
    def _send(self, body: bytes, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        page = NOTICE_PAGE if self.path.startswith("/notice") else MOCK_PAGE
        self._send(page.encode(), "text/html; charset=utf-8")

    def do_POST(self):  # noqa: N802
        self._send(json.dumps(MOCK_GRADES, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def log_message(self, *args):
        pass


@pytest.fixture
def school(monkeypatch):
    server = ThreadingHTTPServer(("127.0.0.1", 0), MockSchool)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    monkeypatch.setenv("KNU_IMPORT_ENABLED", "1")
    monkeypatch.setenv("KNU_IMPORT_START_URL", f"http://127.0.0.1:{port}/webview/main/Main.knu")
    monkeypatch.setenv("KNU_IMPORT_ALLOWED_HOSTS", "127.0.0.1")
    monkeypatch.delenv("KNU_IMPORT_ALLOW_REMOTE", raising=False)
    manager = KnuSessionManager()
    monkeypatch.setattr(knu_session, "manager", manager)
    yield manager
    manager.shutdown()
    server.shutdown()


def call(manager, coroutine):
    return manager._worker.run_blocking(coroutine, timeout=15)


def center(manager, token, selector):
    page = manager._sessions[token].page
    box = call(manager, page.locator(selector).bounding_box())
    return {"x": box["x"] + box["width"] / 2, "y": box["y"] + box["height"] / 2}


def test_login_shortcut_fills_school_login_and_finishes(school, caplog):
    caplog.set_level(logging.DEBUG)
    client = TestClient(app, client=("127.0.0.1", 50002))
    started = client.post("/import/knu/start", json={"consent": True})
    if started.status_code == 503:
        pytest.skip(started.json()["detail"])
    headers = {"X-Import-Session": started.json()["session"]}

    # 로그인 칸이 보이면 frame 이 알려 준다. 화면 캡처는 받지 않는다.
    deadline = time.time() + 15
    while time.time() < deadline and not client.post("/import/knu/frame", json={"image": False}, headers=headers).json()["login_form"]:
        time.sleep(0.3)
    secret = "pw-Secret-7310"
    response = client.post("/import/knu/login", json={"user_id": "student", "password": secret}, headers=headers)
    assert response.status_code == 200, response.text

    frame, deadline = {}, time.time() + 30
    while time.time() < deadline:
        frame = client.post("/import/knu/frame", json={"image": False}, headers=headers).json()
        if frame["finished"]:
            break
        time.sleep(0.3)
    assert frame["finished"] and frame["login_form"] is False
    assert frame["image"] is None
    assert [c["code"] for c in frame["courses"]] == ["COMP0201", "CLTR0001"]
    # 로그인 칸이 없으면 409 로 알려 주고, 비밀번호는 응답과 로그 어디에도 없다.
    again = client.post("/import/knu/login", json={"user_id": "student", "password": secret}, headers=headers)
    assert again.status_code == 409 and secret not in again.text
    client.post("/import/knu/stop", headers=headers)
    assert secret not in caplog.text


def test_full_flow_against_a_mock_school(school, caplog):
    caplog.set_level(logging.DEBUG)
    client = TestClient(app, client=("127.0.0.1", 50001))
    started = client.post("/import/knu/start", json={"consent": True})
    if started.status_code == 503:
        pytest.skip(started.json()["detail"])
    assert started.status_code == 200, started.text
    token = started.json()["session"]
    headers = {"X-Import-Session": token}
    send = lambda body: client.post("/import/knu/input", json=body, headers=headers)
    first_context = school._sessions[token].context
    main = first_context.pages[0]  # 다 읽으면 브라우저를 닫으므로 미리 잡아 둔다

    # 학생이 원격 화면에서 직접 로그인한다 (클릭과 글자 입력을 API 로 보낸다).
    secret = "pw-Secret-4821"
    assert send({"type": "click", **center(school, token, "#uid")}).status_code == 200
    assert send({"type": "text", "text": "student"}).status_code == 200
    assert send({"type": "click", **center(school, token, "#pwd")}).status_code == 200
    assert send({"type": "text", "text": secret}).status_code == 200
    assert send({"type": "click", **center(school, token, "#login-btn")}).status_code == 200

    # 학생은 더 누르지 않는다. 자동으로 성적 → 학기성적 → 이수성적 조회 → 조회 버튼까지 눌러 응답을 읽는다.
    began = time.time()
    deadline = began + 60
    frame, statuses = {}, []
    while time.time() < deadline:
        frame = client.post("/import/knu/frame", headers=headers).json()
        if not statuses or statuses[-1][1] != frame["status"]:
            statuses.append((round(time.time() - began, 1), frame["status"]))
        if frame["finished"]:
            break
        time.sleep(0.5)
    assert frame["finished"], statuses
    assert time.time() - began < 10, statuses  # 고치기 전에는 약 14초
    assert set(school._sessions[token].visited_menus) == {"성적", "학기성적"}, statuses  # 화면 폴링이 문구를 놓칠 수 있어 기록으로 확인
    assert school._sessions[token].fallback_used is False  # 학사행정은 누르지 않았다
    assert school._sessions[token].query_clicks == 1  # 조회 버튼을 자동으로 한 번 눌렀다 (공지 팝업이 떠 있어도)
    # 다 읽으면 학교 세션(쿠키)을 담은 브라우저를 바로 닫는다. 읽은 과목은 남는다.
    deadline = time.time() + 5
    while (school._sessions[token].context is not None or first_context.pages) and time.time() < deadline:
        time.sleep(0.1)
    assert school._sessions[token].context is None
    assert not first_context.pages and main.is_closed()
    assert [(c["code"], c["credits"], c["category"]) for c in frame["courses"]] == [
        ("COMP0201", 3.0, "전공필수"),
        ("CLTR0001", 2.0, "교양"),
    ]
    assert frame["duplicates"] == ["COMP0201"]
    assert base64.b64decode(frame["image"]).startswith(b"\xff\xd8")  # JPEG 화면
    after = client.post("/import/knu/frame", headers=headers).json()
    assert after["finished"] and [c["code"] for c in after["courses"]] == ["COMP0201", "CLTR0001"]
    # 성적은 내보내지 않는다 (화면 이미지 문자열은 우연히 같은 글자를 담을 수 있어 빼고 본다)
    exported = json.dumps({key: value for key, value in frame.items() if key != "image"}, ensure_ascii=False)
    assert "gradsGradCd" not in exported
    assert all(grade not in exported for grade in ("A+", "B0", "C+"))

    # 두 번째 학생은 첫 번째 학생의 로그인(쿠키)을 볼 수 없다.
    other = client.post("/import/knu/start", json={"consent": True}).json()["session"]
    other_page = school._sessions[other].page
    # 시작 응답은 학교 페이지가 다 열리기 전에 오므로, 로그인 칸이 보일 때까지 기다린다.
    # (첫 번째 학생의 쿠키가 보인다면 로그인 칸이 숨겨져 여기서 실패한다)
    call(school, other_page.wait_for_selector("#login", state="visible", timeout=10_000))

    # 원격 브라우저는 허용한 주소 밖에 머물지 못한다 (localhost 는 허용 목록에 없다).
    outside = other_page.url.replace("127.0.0.1", "localhost")
    call(school, other_page.evaluate(f"location.href = {outside!r}"))
    seen, deadline = [], time.time() + 10
    while time.time() < deadline:
        seen.append(client.post("/import/knu/frame", headers={"X-Import-Session": other}).json()["status"])
        if other_page.url.startswith("http://127.0.0.1") and any("되돌렸습니다" in item for item in seen):
            break
        time.sleep(0.1)
    assert other_page.url.startswith("http://127.0.0.1"), other_page.url
    assert any("되돌렸습니다" in item for item in seen), seen

    # 연결을 끊으면 브라우저와 결과가 사라진다.
    contexts = [school._sessions[other].context]
    for item in (token, other):
        assert client.post("/import/knu/stop", headers={"X-Import-Session": item}).json()["closed"] is True
    assert school.session_count() == 0
    assert school._browser is not None  # 다음 시작을 빠르게 하려고 Chrome 은 잠시 켜 둔다
    assert all(not context.pages for context in contexts)
    assert client.post("/import/knu/frame", headers=headers).status_code == 404

    assert secret not in caplog.text
