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


def test_prayer_returns_ledger_surface():
    response = client.get("/me/prayer")
    assert response.status_code == 200
    assert "data-testid=\"prayer-tabs\"" in response.text
    assert "data-testid=\"prayer-list\"" in response.text
    assert "data-testid=\"prayer-new-petition\"" in response.text
    assert "data-testid=\"weigh-list\"" in response.text


def test_timeline_returns_arc_surface():
    response = client.get("/me/timeline")
    assert response.status_code == 200
    assert "data-testid=\"timeline-list\"" in response.text
    assert "data-testid=\"timeline-headline\"" in response.text


def test_pwa_shell_is_wired():
    """B3: manifest + icon are referenced by the base template and the
    service worker serves from the root so its scope covers the whole app."""
    body = client.get("/me").text
    assert "/static/manifest.json" in body
    assert "/static/icon.svg" in body
    assert "serviceWorker" in body

    sw = client.get("/sw.js")
    assert sw.status_code == 200
    assert "javascript" in sw.headers["content-type"]
    assert client.get("/static/manifest.json").status_code == 200


def test_year_returns_formation_year_surface():
    response = client.get("/me/year")
    assert response.status_code == 200
    assert "data-testid=\"year-headline\"" in response.text
    assert "data-testid=\"year-numbers\"" in response.text
    assert "data-testid=\"year-lines\"" in response.text


def test_cohort_overview_returns_overview_surface():
    response = client.get("/cohort")
    assert response.status_code == 200
    assert "data-testid=\"cohort-chart\"" in response.text
    assert "data-testid=\"cohort-snippet-list\"" in response.text
    assert "data-testid=\"cohort-go-to-triage\"" in response.text


def test_cohort_groups_returns_planner_surface():
    response = client.get("/cohort/groups")
    assert response.status_code == 200
    assert "data-testid=\"groups-roster\"" in response.text
    assert "data-testid=\"group-alpha\"" in response.text
    assert "data-testid=\"groups-distribute\"" in response.text
    assert "data-testid=\"groups-confirm\"" in response.text


def test_subnav_active_state_set_per_route():
    me_resp = client.get("/me").text
    chat_resp = client.get("/me/chat").text
    arc_resp = client.get("/me/timeline").text
    cohort_resp = client.get("/cohort").text
    triage_resp = client.get("/cohort/triage").text
    groups_resp = client.get("/cohort/groups").text
    prayer_resp = client.get("/me/prayer").text
    assert "aria-current=\"page\">Today" in me_resp
    assert "aria-current=\"page\">Mentor" in chat_resp
    assert "aria-current=\"page\">Prayer" in prayer_resp
    assert "aria-current=\"page\">Arc" in arc_resp
    assert "aria-current=\"page\">Cohort" in cohort_resp
    assert "aria-current=\"page\">Triage" in triage_resp
    assert "aria-current=\"page\">Groups" in groups_resp


def test_seminarian_subnav_includes_arc_after_p2():
    response = client.get("/me").text
    assert ">Today<" in response and ">Mentor<" in response and ">Arc<" in response
    assert ">Prayer<" in response


def test_director_subnav_includes_cohort_and_groups_after_p2():
    response = client.get("/cohort/triage").text
    assert ">Cohort<" in response and ">Triage<" in response and ">Groups<" in response


def test_per_page_assets_are_referenced():
    """Each page must reference its own CSS + JS files. Catches regressions
    where a template forgets to include its assets."""
    pairs = [
        ("/", "door.css"),
        ("/me", "me.css"),
        ("/me", "me.js"),
        ("/me/chat", "chat.css"),
        ("/me/chat", "chat.js"),
        ("/me/prayer", "prayer.css"),
        ("/me/prayer", "prayer.js"),
        ("/me/timeline", "timeline.css"),
        ("/me/timeline", "timeline.js"),
        ("/me/year", "year.css"),
        ("/me/year", "year.js"),
        ("/cohort", "cohort_overview.css"),
        ("/cohort", "cohort_overview.js"),
        ("/cohort/triage", "triage.css"),
        ("/cohort/triage", "triage.js"),
        ("/cohort/groups", "cohort_groups.css"),
        ("/cohort/groups", "cohort_groups.js"),
        ("/students/stu-anna-t", "profile.css"),
        ("/students/stu-anna-t", "profile.js"),
    ]
    for path, asset in pairs:
        body = client.get(path).text
        assert asset in body, f"{path} does not reference {asset}"
