"""C4 (shared 40-day journey) + C5 (counts-only pulse note)."""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.services import journey, prayer, pulse
from backend.fixtures import cohort as cohort_fixtures

client = TestClient(app)


# ---- journey ----

def test_journey_day_derives_from_start(monkeypatch):
    monkeypatch.setenv("KC_JOURNEY_START", "2026-06-22")
    j = journey.current_journey(today=date(2026, 7, 3))
    assert (j["day"], j["completed"], j["upcoming"]) == (12, False, False)
    assert j["theme"] == journey.WEEKLY_THEMES[1]  # day 12 → second week


def test_journey_clamps_outside_the_window(monkeypatch):
    monkeypatch.setenv("KC_JOURNEY_START", "2026-01-01")
    done = journey.current_journey(today=date(2026, 7, 3))
    assert done["completed"] is True and done["day"] == 40

    monkeypatch.setenv("KC_JOURNEY_START", "2026-12-01")
    early = journey.current_journey(today=date(2026, 7, 3))
    assert early["upcoming"] is True and early["day"] == 1


def test_journey_bad_env_falls_back_to_demo_default(monkeypatch):
    monkeypatch.setenv("KC_JOURNEY_START", "not-a-date")
    j = journey.current_journey(today=date(2026, 7, 3))
    assert j["day"] == 12  # demo default: started 11 days ago


def test_journey_endpoint():
    body = client.get("/api/journey").json()
    assert body["total_days"] == 40
    assert 1 <= body["day"] <= 40
    assert body["theme"]


# ---- pulse note ----

@pytest.fixture(autouse=True)
def fake_llm(monkeypatch):
    monkeypatch.setenv("LLM_FAKE_RESPONSE", "Hold the three gently this week.")
    prayer.reset()
    yield
    prayer.reset()


def test_pulse_prompt_is_counts_only():
    students = cohort_fixtures.list_students()
    pr = prayer.submit_prayer(student_id=students[0]["id"], petition="A very private thing.")
    prayer.add_intercession(pr.id, students[1]["id"])
    rows = prayer.cohort_rhythm(s["id"] for s in students)

    prompt = pulse.build_pulse_prompt(students, rows)
    assert "1 petitions" in prompt and "1 intercessions" in prompt
    # The privacy contract: no names, no petition content, ever.
    assert "A very private thing" not in prompt
    for s in students:
        assert s["name"] not in prompt


def test_pulse_note_endpoint_composes_via_chain():
    body = client.get(f"/api/cohorts/{cohort_fixtures.COHORT_ID}/pulse-note").json()
    assert body["note"] == "Hold the three gently this week."


def test_pulse_note_unknown_cohort_is_404():
    assert client.get("/api/cohorts/nope/pulse-note").status_code == 404
