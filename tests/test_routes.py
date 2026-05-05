"""Route smoke tests for the redesigned surfaces. Confirms each Jinja-rendered
HTML page returns 200 and contains a canonical test-id, so regressions on the
template wiring or the FastAPI route mapping fail loudly."""

from fastapi.testclient import TestClient

from backend.app import app


client = TestClient(app)


def test_root_returns_door():
    response = client.get("/")
    assert response.status_code == 200
    assert "role-card-seminarian" in response.text
    assert "role-card-director" in response.text


def test_me_returns_seminarian_morning():
    response = client.get("/me")
    assert response.status_code == 200
    assert "data-testid=\"me-status-line\"" in response.text
    assert "data-testid=\"me-prompt\"" in response.text
    assert "data-testid=\"me-talk-mentor\"" in response.text


def test_chat_returns_chat_surface():
    response = client.get("/me/chat")
    assert response.status_code == 200
    assert "data-testid=\"chat-form\"" in response.text
    assert "data-testid=\"chat-thread\"" in response.text
    assert "data-testid=\"memory-pills\"" in response.text


def test_cohort_triage_returns_triage_surface():
    response = client.get("/cohort/triage")
    assert response.status_code == 200
    assert "data-testid=\"triage-list\"" in response.text
    assert "data-testid=\"triage-cohort-name\"" in response.text


def test_student_profile_returns_profile_surface():
    response = client.get("/students/stu-marcus-r")
    assert response.status_code == 200
    assert "data-testid=\"profile-header\"" in response.text
    assert "data-testid=\"tab-reflections\"" in response.text
    assert "data-testid=\"profile-log-outcome\"" in response.text
    # student_id must be passed into the template so per-page JS can fetch it.
    assert "stu-marcus-r" in response.text


def test_admin_workbench_route_serves_index_html():
    response = client.get("/admin/workbench")
    assert response.status_code == 200
    assert "data-testid=\"dropout-form\"" in response.text


def test_subnav_active_state_set_per_route():
    me_resp = client.get("/me").text
    chat_resp = client.get("/me/chat").text
    # Today should be active on /me, Mentor active on /me/chat.
    assert "aria-current=\"page\">Today" in me_resp
    assert "aria-current=\"page\">Mentor" in chat_resp


def test_per_page_assets_are_referenced():
    """Each page must reference its own CSS + JS files. Catches regressions
    where a template forgets to include its assets."""
    pairs = [
        ("/", "door.css"),
        ("/me", "me.css"),
        ("/me", "me.js"),
        ("/me/chat", "chat.css"),
        ("/me/chat", "chat.js"),
        ("/cohort/triage", "triage.css"),
        ("/cohort/triage", "triage.js"),
        ("/students/stu-anna-t", "profile.css"),
        ("/students/stu-anna-t", "profile.js"),
    ]
    for path, asset in pairs:
        body = client.get(path).text
        assert asset in body, f"{path} does not reference {asset}"
