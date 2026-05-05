from fastapi.testclient import TestClient

from backend.app import app


client = TestClient(app)


def test_landing_page_serves_public_product_ui():
    response = client.get("/")

    assert response.status_code == 200
    assert "Kingdom Come" in response.text
    assert "Predictive formation intelligence" in response.text
    assert "data-testid=\"dropout-form\"" in response.text
    assert "data-testid=\"chat-result\"" in response.text


def test_static_assets_are_served():
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "submitDropoutRisk" in response.text
    assert "submitChat" in response.text
