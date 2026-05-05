from fastapi.testclient import TestClient

from backend.app import app
from backend.models.outcome import MinistryOutcome


client = TestClient(app)


def test_health_endpoint_reports_ready():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "seminary-formation-platform-v7"}


def test_predictive_endpoint_scores_dropout_risk():
    response = client.post("/predictive/dropout-risk", json={"engagement": 0.2, "reflection_count": 1})

    assert response.status_code == 200
    assert response.json()["level"] == "high"


def test_curriculum_endpoint_recommends_content():
    response = client.post("/curriculum/recommendations", json={"calling": "evangelism"})

    assert response.status_code == 200
    assert response.json() == {"recommendations": ["mission_theology", "field_practice", "general_theology"]}


def test_outcome_model_is_importable_and_named():
    assert MinistryOutcome.__tablename__ == "ministry_outcomes"
