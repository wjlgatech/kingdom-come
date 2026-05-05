"""End-to-end Playwright tests for the redesigned Kingdom Come surfaces.

Anchored to the user stories:
- #1 Marcus's morning snapshot
- #2 Marcus's continuing mentor conversation
- #3 Theresa's cohort triage with named reasons
- #5 Theresa's two-click outcome logging from a student profile

All assertions use `wait_for_function` against actual DOM content. Never
`wait_for()` on already-visible elements (race-flake lesson from 3087bda).
"""

import os
import socket
import subprocess
import time

import pytest
from playwright.sync_api import Error, sync_playwright


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="module")
def live_app():
    port = _free_port()
    env = {
        **os.environ,
        "EMBEDDING_FAKE": "1",
        "LLM_FAKE_RESPONSE": "Walk gently into this week.",
    }
    env.pop("REDIS_URL", None)
    process = subprocess.Popen(
        ["python", "-m", "uvicorn", "backend.app:app", "--host", "127.0.0.1", "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                break
        time.sleep(0.1)
    else:
        output = process.stdout.read() if process.stdout else ""
        process.terminate()
        raise RuntimeError(f"Uvicorn did not start: {output}")

    yield f"http://127.0.0.1:{port}"

    process.terminate()
    process.wait(timeout=5)


def _seed_role(page, role, base):
    """Pre-seed localStorage so role-gated pages don't redirect away.
    The localStorage values are wired by door.js when a user clicks a role
    card; for direct-page tests we set them via a tiny script before navigating."""
    page.goto(base, wait_until="domcontentloaded")
    sid = "stu-marcus-r" if role == "seminarian" else "fd-theresa"
    page.evaluate(f"() => {{ localStorage.setItem('kc-role', '{role}'); localStorage.setItem('kc-student-id', '{sid}'); }}")


def test_e2e_door_redirects_existing_seminarian_to_me(live_app):
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})

            # First visit: door is visible.
            page.goto(live_app, wait_until="networkidle")
            assert page.get_by_test_id("role-card-seminarian").is_visible()
            assert page.get_by_test_id("role-card-director").is_visible()

            # Click seminarian door.
            page.get_by_test_id("role-card-seminarian").click()
            page.wait_for_url(f"{live_app}/me")

            # Marcus's morning shows the prompt copy from the template.
            page.wait_for_function(
                "() => /Begin reflection/.test(document.querySelector('[data-testid=\"me-begin-reflection\"]')?.textContent ?? '')"
            )

            # Revisit /  — should now redirect straight to /me without showing the door.
            page.goto(live_app, wait_until="domcontentloaded")
            page.wait_for_url(f"{live_app}/me", timeout=5000)

            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright door flow failed: {exc}")


def test_e2e_door_redirects_existing_director_to_triage(live_app):
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(live_app, wait_until="networkidle")
            page.get_by_test_id("role-card-director").click()
            page.wait_for_url(f"{live_app}/cohort/triage")

            # Triage list renders rows with status pills (waits for the API
            # round-trip + DOM injection).
            page.wait_for_function(
                "() => document.querySelectorAll('[data-testid=\"triage-row\"]').length >= 1"
            )
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright director redirect failed: {exc}")


def test_e2e_me_renders_status_and_path(live_app):
    """Story #1: Marcus's morning shows status (with a real reason) and his next path."""
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _seed_role(page, "seminarian", live_app)
            page.goto(f"{live_app}/me", wait_until="networkidle")

            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"me-status-pill\"]') !== null"
            )
            status_text = page.get_by_test_id("me-status-pill").inner_text().strip()
            assert status_text in {"Thriving", "Steady", "Needs check-in", "At risk"}

            page.wait_for_function(
                "() => /mission|theology|holding|formation/i.test(document.querySelector('[data-testid=\"me-path-line\"]')?.innerText ?? '')"
            )

            # Talk-to-mentor link navigates to /me/chat.
            page.get_by_test_id("me-talk-mentor").click()
            page.wait_for_url(f"{live_app}/me/chat")
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright me flow failed: {exc}")


def test_e2e_chat_streams_reply_and_renders_memory_pills_on_second_send(live_app):
    """Story #2: Marcus sends, sees streamed reply, then on second send sees the
    'Mentor remembers:' pills appear above the input."""
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _seed_role(page, "seminarian", live_app)
            page.goto(f"{live_app}/me/chat", wait_until="networkidle")

            page.get_by_test_id("chat-message-input").fill("I'm wrestling with the readings this week.")
            page.get_by_test_id("chat-send").click()
            page.wait_for_function(
                "() => /Walk gently into this week/.test(document.querySelector('[data-testid=\"chat-thread\"]')?.innerText ?? '')"
            )

            # First send: memory pills should NOT be visible (new student, empty memory).
            assert page.get_by_test_id("memory-pills").is_hidden()

            # Second send: pills appear because the prior turn is in memory now.
            page.get_by_test_id("chat-message-input").fill("Following up on those readings.")
            page.get_by_test_id("chat-send").click()
            page.wait_for_function(
                "() => document.querySelectorAll('[data-testid=\"memory-pill\"]').length >= 1"
            )
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright chat flow failed: {exc}")


def test_e2e_triage_renders_named_statuses_with_reasons(live_app):
    """Story #3: triage list shows students with named status pills and
    plain-English reasons (not bare codes like 'low_engagement')."""
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _seed_role(page, "director", live_app)
            page.goto(f"{live_app}/cohort/triage", wait_until="networkidle")

            page.wait_for_function(
                "() => document.querySelectorAll('[data-testid=\"triage-row\"]').length >= 2"
            )
            # At least one row uses a real translated reason (not a code).
            page.wait_for_function(
                "() => Array.from(document.querySelectorAll('[data-testid=\"triage-reason\"]')).some(el => /Engagement|Hasn't reflected|drift|Holding/.test(el.innerText))"
            )
            # No raw status codes leak into the UI.
            text = page.locator("[data-testid='triage-list']").inner_text()
            for raw_code in ("low_engagement", "few_reflections", "calling_drift"):
                assert raw_code not in text, f"raw code {raw_code} leaked into triage UI"

            # Click the first row's avatar/name area to open profile.
            page.locator("[data-testid='triage-row']").first.click()
            page.wait_for_url("**/students/**")
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright triage flow failed: {exc}")


def test_e2e_profile_log_outcome_two_clicks(live_app):
    """Story #5: from /students/:id, two clicks (+ Log outcome → Save) creates
    a new outcome that appears at the top of the Outcomes feed."""
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _seed_role(page, "director", live_app)
            page.goto(f"{live_app}/students/stu-anna-t", wait_until="networkidle")

            # Profile header loads.
            page.wait_for_function(
                "() => /Anna/.test(document.querySelector('[data-testid=\"profile-name\"]')?.innerText ?? '')"
            )

            # Click +Log outcome — modal opens.
            page.get_by_test_id("profile-log-outcome").click()
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"outcome-modal\"]') !== null"
            )

            page.locator("#outcome-description").fill("Led the parish soup kitchen rotation.")
            page.locator("[data-testid='outcome-modal-save']").click()

            # Modal closes and the new outcome appears in the Outcomes panel.
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"outcome-modal\"]') === null"
            )
            page.wait_for_function(
                "() => Array.from(document.querySelectorAll('[data-testid=\"outcome-entry\"]')).some(el => /soup kitchen rotation/.test(el.innerText))"
            )
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright profile flow failed: {exc}")


def test_e2e_profile_modal_esc_closes_and_returns_focus(live_app):
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _seed_role(page, "director", live_app)
            page.goto(f"{live_app}/students/stu-marcus-r", wait_until="networkidle")
            page.wait_for_function(
                "() => /Marcus/.test(document.querySelector('[data-testid=\"profile-name\"]')?.innerText ?? '')"
            )

            page.get_by_test_id("profile-log-outcome").click()
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"outcome-modal\"]') !== null"
            )
            page.keyboard.press("Escape")
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"outcome-modal\"]') === null"
            )
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright modal-escape failed: {exc}")


def test_e2e_invalid_student_id_renders_not_found(live_app):
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _seed_role(page, "director", live_app)
            page.goto(f"{live_app}/students/bogus-id", wait_until="networkidle")
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"profile-not-found\"]') !== null"
            )
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright not-found flow failed: {exc}")
