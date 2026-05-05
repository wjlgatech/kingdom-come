from fastapi.testclient import TestClient

from backend.app import app


client = TestClient(app)


def test_landing_page_serves_role_doors():
    response = client.get("/")

    assert response.status_code == 200
    assert "Kingdom Come" in response.text
    assert "data-testid=\"role-card-seminarian\"" in response.text
    assert "data-testid=\"role-card-director\"" in response.text
    assert "data-testid=\"engineer-workbench-link\"" in response.text


def test_admin_workbench_preserves_engineer_dashboard():
    response = client.get("/admin/workbench")

    assert response.status_code == 200
    assert "data-testid=\"dropout-form\"" in response.text
    assert "data-testid=\"chat-result\"" in response.text


def test_static_assets_are_served():
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "submitDropoutRisk" in response.text
    assert "submitChat" in response.text


def test_design_tokens_served():
    response = client.get("/static/tokens.css")

    assert response.status_code == 200
    assert "--accent: #7c2d3a" in response.text


def test_status_helper_served():
    response = client.get("/static/status.js")

    assert response.status_code == 200
    assert "statusFromRisk" in response.text
    assert "reasonsToSentence" in response.text
