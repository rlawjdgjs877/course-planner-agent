"""나의 시간표 챗봇. AI 없이(규칙) 설명하고, 말대로 시간표를 다시 만드는지 본다."""

from fastapi.testclient import TestClient

from app.agent import plan_chat
from app.main import app
from app.schemas import GenerateTimetableRequest
from app.services import planner
from app.services.course_repository import load_courses

client = TestClient(app)
no_ai = lambda *_: None  # noqa: E731


def first_candidate():
    request = GenerateTimetableRequest(track="advanced", grade=2)
    response = planner.generate(request, load_courses())
    assert response.candidates
    return request, response.candidates[0]


def test_explains_why_without_message():
    request, candidate = first_candidate()
    answer = plan_chat.handle(plan_chat.PlanChatRequest(request=request, candidate_id=candidate.id), load_courses(), ask=no_ai)
    assert not answer.applied
    assert f"{candidate.total_credits:g}학점" in answer.reply
    assert all(section.name in answer.reply for section in candidate.sections)


def test_free_day_and_remove_course_rebuild_timetable():
    request, candidate = first_candidate()
    busy = next(m.day for s in candidate.sections for m in s.meetings)
    answer = plan_chat.handle(plan_chat.PlanChatRequest(message=f"{busy}요일 비워줘", request=request, candidate_id=candidate.id), load_courses(), ask=no_ai)
    assert answer.applied and busy in answer.request.free_days
    assert all(m.day != busy for s in answer.response.candidates[0].sections for m in s.meetings)

    gone = candidate.sections[0]
    answer = plan_chat.handle(plan_chat.PlanChatRequest(message=f"{gone.name} 빼줘", request=request, candidate_id=candidate.id), load_courses(), ask=no_ai)
    assert answer.applied and gone.course_code in answer.request.exclude
    assert all(s.course_code != gone.course_code for s in answer.response.candidates[0].sections)


def test_rules_parse_common_phrases():
    edit = plan_chat.parse_rules("아침 수업 싫어, 15학점으로 해줘", None, [])
    assert (edit.no_class_before, edit.target_credits) == (10, 15)
    assert plan_chat.parse_rules("금요일 빼줘", None, []).free_days == ["금"]
    assert plan_chat.parse_rules("금요일 수업 있어도 돼", None, []).unfree_days == ["금"]


def test_unknown_message_keeps_request():
    request, candidate = first_candidate()
    answer = plan_chat.handle(plan_chat.PlanChatRequest(message="안녕", request=request, candidate_id=candidate.id), load_courses(), ask=no_ai)
    assert not answer.applied and answer.request == request


def test_endpoint():
    request, candidate = first_candidate()
    body = {"request": request.model_dump(), "candidate_id": candidate.id}
    assert client.post("/tools/chat", json=body).status_code == 200
