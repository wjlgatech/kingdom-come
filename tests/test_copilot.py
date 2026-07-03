"""The in-app Copilot (backend/services/copilot.py + /ws/copilot).

Covers the two contracts that matter: the privacy scoping (director context
is counts/statuses/names — never ledger content; seminarian context is the
asker's own record only) and the WS frame order (context pills → chunks →
done), with the deterministic grounded digest used when no real model is
attached.
"""
import json

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.services import copilot, prayer


@pytest.fixture(autouse=True)
def isolated_state(monkeypatch):
    monkeypatch.setenv("LLM_FAKE_RESPONSE", "Grace and peace.")
    prayer.reset()
    yield
    prayer.reset()


SECRET = "A very private wrestling with my vocation."


def test_director_context_never_contains_ledger_content():
    pr = prayer.submit_prayer(student_id="stu-marcus-r", petition=SECRET, visibility="cohort")
    prayer.add_intercession(pr.id, "stu-luca-b", "Carrying this with you, brother.")

    context = copilot.gather_context("director")
    blob = json.dumps(context, ensure_ascii=False)
    assert SECRET not in blob
    assert "Carrying this with you" not in blob
    # Counts and statuses ARE there — the director sees rhythm, not content.
    assert context["prayer rhythm"]["petitions"] == 1
    assert context["triage"]["students_total"] == 24
    assert any(s["name"] == "Marcus Reilly" for s in context["triage"]["needing_attention"])


def test_seminarian_context_is_own_record_only():
    prayer.submit_prayer(student_id="stu-sarah-k", petition="Sarah's private petition.")
    prayer.submit_prayer(student_id="stu-marcus-r", petition="Marcus's own petition.")

    context = copilot.gather_context("seminarian", "stu-marcus-r")
    blob = json.dumps(context, ensure_ascii=False)
    assert "Sarah" not in blob
    assert context["my track record"]["petitions"] == 1
    assert context["my status"]["name"] == "Marcus Reilly"


def test_unknown_scope_raises():
    with pytest.raises(ValueError):
        copilot.gather_context("admin")
    with pytest.raises(ValueError):
        copilot.gather_context("seminarian")  # no student_id


def test_grounded_digest_uses_true_numbers():
    pr = prayer.submit_prayer(student_id="stu-marcus-r", petition="Steady hands.")
    prayer.mark_answered(pr.id, status="answered_yes", testimony="Held.")

    digest = copilot._grounded_digest("director", copilot.gather_context("director"))
    assert "of 24 students" in digest
    assert "1 petitions (1 answered)" in digest

    my = copilot._grounded_digest(
        "seminarian", copilot.gather_context("seminarian", "stu-marcus-r")
    )
    assert "1 petitions (1 answered favorably)" in my
    assert "Day" in my  # journey line


def _drain(ws):
    context, chunks = None, []
    while True:
        msg = ws.receive_json()
        if msg.get("done"):
            return context, chunks, None
        if "error" in msg:
            return context, chunks, msg["error"]
        if "context" in msg:
            context = msg["context"]
            continue
        chunks.append(msg["chunk"])


def test_ws_copilot_frame_order_and_grounding():
    client = TestClient(app)
    with client.websocket_connect("/ws/copilot") as ws:
        ws.send_json({"role": "director", "question": "Who needs me this week?"})
        context, chunks, error = _drain(ws)
    assert error is None
    assert context == ["triage", "prayer rhythm", "engagement", "journey"]
    text = "".join(chunks)
    assert "of 24 students" in text  # grounded digest, not the canned fake line


def test_ws_copilot_validates_input():
    client = TestClient(app)
    with client.websocket_connect("/ws/copilot") as ws:
        ws.send_json({"role": "pope", "question": "hi"})
        assert "required" in ws.receive_json()["error"]
        ws.send_json({"role": "seminarian", "question": "hi"})
        assert "student_id" in ws.receive_json()["error"]
        # Socket stays usable after errors.
        ws.send_json({"role": "seminarian", "question": "How am I doing?", "student_id": "stu-marcus-r"})
        context, chunks, error = _drain(ws)
    assert error is None
    assert "my status" in context
