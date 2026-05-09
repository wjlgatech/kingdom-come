"""Tests for the agent-facing read endpoints (`/students`, `/students/{id}`,
`/cohorts/{id}`, `/cohorts/{id}/outcomes`). These are the data the MCP server
exposes — the contract here is what agents see.
"""

from fastapi.testclient import TestClient

from backend.app import app
from backend.fixtures import cohort as cohort_fixtures


client = TestClient(app)


def test_list_students_returns_full_cohort():
    response = client.get("/api/students")
    assert response.status_code == 200
    body = response.json()
    assert "students" in body
    assert len(body["students"]) == len(cohort_fixtures.COHORT)
    ids = {s["id"] for s in body["students"]}
    assert "stu-marcus-r" in ids
    assert "stu-anna-t" in ids


def test_list_students_filters_by_cohort_id():
    response = client.get("/api/students", params={"cohort_id": cohort_fixtures.COHORT_ID})
    assert response.status_code == 200
    assert len(response.json()["students"]) == len(cohort_fixtures.COHORT)


def test_list_students_unknown_cohort_returns_empty():
    response = client.get("/api/students", params={"cohort_id": "nope"})
    assert response.status_code == 200
    assert response.json() == {"students": []}


def test_get_student_returns_profile_aggregate():
    response = client.get("/api/students/stu-marcus-r")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "stu-marcus-r"
    assert body["name"] == "Marcus Reilly"
    assert body["calling"] == ["evangelism"]
    assert isinstance(body["reflections"], list) and len(body["reflections"]) >= 1
    assert isinstance(body["risk_history"], list) and len(body["risk_history"]) >= 1


def test_get_student_unknown_id_returns_404():
    response = client.get("/api/students/bogus")
    assert response.status_code == 404
    assert "bogus" in response.json()["detail"]


def test_get_cohort_returns_meta_with_director():
    response = client.get(f"/api/cohorts/{cohort_fixtures.COHORT_ID}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == cohort_fixtures.COHORT_ID
    assert body["student_count"] == len(cohort_fixtures.COHORT)
    assert body["director"]["id"] == "fd-theresa"


def test_get_cohort_unknown_id_returns_404():
    response = client.get("/api/cohorts/nope")
    assert response.status_code == 404


def test_list_cohort_outcomes_returns_sorted_outcomes():
    response = client.get(f"/api/cohorts/{cohort_fixtures.COHORT_ID}/outcomes")
    assert response.status_code == 200
    outcomes = response.json()["outcomes"]
    # Anna has two outcomes; David has one. Total = 3.
    assert len(outcomes) == 3
    # Sorted by date desc: 2026-04-18, 2026-03-30, 2026-03-21.
    assert [o["date"] for o in outcomes] == ["2026-04-18", "2026-03-30", "2026-03-21"]
    # Each row carries the student_id (so agents can join back to /students).
    assert all("student_id" in o for o in outcomes)


def test_list_cohort_outcomes_unknown_cohort_returns_404():
    response = client.get("/api/cohorts/nope/outcomes")
    assert response.status_code == 404
