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
import sys
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
        "VOICE_FAKE_TEXT": "Give me courage for Thursday.",
    }
    env.pop("REDIS_URL", None)
    env.pop("KC_DEMO_SEED", None)  # tests assert on empty ledgers
    # DEVNULL, never PIPE: nothing drains the pipe during the run, so uvicorn's
    # per-request access log fills the 64KB buffer after ~17 tests and the
    # server freezes mid-suite (blocked stdout write → connection resets).
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app:app", "--host", "127.0.0.1", "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                break
        time.sleep(0.1)
    else:
        process.terminate()
        raise RuntimeError("Uvicorn did not start (run it by hand to see why)")

    yield f"http://127.0.0.1:{port}"

    process.terminate()
    process.wait(timeout=5)


def _seed_role(page, role, base):
    """Pre-seed localStorage so role-gated pages don't redirect away.
    The localStorage values are wired by door.js when a user clicks a role
    card; for direct-page tests we set them via a tiny script before navigating."""
    page.goto(base, wait_until="domcontentloaded")
    sid = "stu-marcus-r" if role == "seminarian" else "fd-theresa"
    page.evaluate(
        f"() => {{ localStorage.setItem('kc-role', '{role}');"
        f" localStorage.setItem('kc-student-id', '{sid}');"
        # Pre-dismiss the first-run tour so page tests stay focused on their
        # surface; the tour has its own dedicated test.
        " localStorage.setItem('kc-tour-me', 'done');"
        " localStorage.setItem('kc-tour-cohort', 'done'); }"
    )


def test_e2e_door_redirects_existing_seminarian_to_me(live_app):
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})

            # First visit: door is visible.
            page.goto(live_app, wait_until="domcontentloaded")
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
            page.goto(live_app, wait_until="domcontentloaded")
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
            page.goto(f"{live_app}/me", wait_until="domcontentloaded")

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
            page.goto(f"{live_app}/me/chat", wait_until="domcontentloaded")

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


def test_e2e_voice_mic_mounts_when_backend_available(live_app):
    """Voice input: the mic button appears next to the chat input because the
    server's health probe reports a live transcription tier (VOICE_FAKE_TEXT
    in this fixture). Actual audio capture is covered by the fake-media rig
    pattern (enduser-webtest), not here."""
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _seed_role(page, "seminarian", live_app)
            page.goto(f"{live_app}/me/chat", wait_until="domcontentloaded")
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"voice-mic\"]') !== null"
            )
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright voice mount failed: {exc}")


def test_e2e_manage_memory_lists_and_forgets(live_app):
    """REC-3 transparency: 'Manage memory' opens the list of what the mentor
    remembers, and forgetting one removes it. Runs after the pills test on the
    same module server, so stu-marcus-r already has remembered turns."""
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _seed_role(page, "seminarian", live_app)
            page.goto(f"{live_app}/me/chat", wait_until="domcontentloaded")

            page.get_by_test_id("chat-manage-memory").click()
            page.wait_for_function(
                "() => document.querySelectorAll('[data-testid=\"memory-row\"]').length >= 1"
            )
            before = len(page.query_selector_all("[data-testid='memory-row']"))

            page.query_selector_all("[data-testid='memory-forget']")[0].click()
            page.wait_for_function(
                "(n) => document.querySelectorAll('[data-testid=\"memory-row\"]').length === n - 1"
                " || document.querySelector('[data-testid=\"memory-empty\"]') !== null",
                arg=before,
            )
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright manage-memory flow failed: {exc}")


def test_e2e_triage_renders_named_statuses_with_reasons(live_app):
    """Story #3: triage list shows students with named status pills and
    plain-English reasons (not bare codes like 'low_engagement')."""
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _seed_role(page, "director", live_app)
            page.goto(f"{live_app}/cohort/triage", wait_until="domcontentloaded")

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
            page.goto(f"{live_app}/students/stu-anna-t", wait_until="domcontentloaded")

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
            page.goto(f"{live_app}/students/stu-marcus-r", wait_until="domcontentloaded")
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


def test_e2e_timeline_renders_weekly_arc(live_app):
    """P2: Marcus's formation arc shows weekly cards with reflections + status."""
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _seed_role(page, "seminarian", live_app)
            page.goto(f"{live_app}/me/timeline", wait_until="domcontentloaded")

            page.wait_for_function(
                "() => document.querySelectorAll('[data-testid=\"timeline-week\"]').length >= 3"
            )
            # The most recent week (first card) gets a reflection from PROFILE_FIXTURES.
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"timeline-reflection\"]') !== null"
            )
            # Subnav has Arc active.
            arc_active = page.locator("a[aria-current='page']").first.inner_text().strip()
            assert arc_active == "Arc"
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright timeline flow failed: {exc}")


def test_e2e_cohort_overview_renders_chart_and_snippet(live_app):
    """P2: Director's cohort overview shows chart + flagged-students snippet."""
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _seed_role(page, "director", live_app)
            page.goto(f"{live_app}/cohort", wait_until="domcontentloaded")

            # Chart SVG renders synchronously; snippet rows wait for fetch.
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"cohort-chart-svg\"]') !== null"
            )
            page.wait_for_function(
                "() => document.querySelectorAll('[data-testid=\"cohort-snippet-row\"]').length >= 1"
            )
            # Paragraph is no longer a skeleton placeholder.
            page.wait_for_function(
                "() => /students/.test(document.querySelector('[data-testid=\"cohort-paragraph\"]')?.innerText ?? '')"
            )
            # "Open triage →" link goes to /cohort/triage.
            page.get_by_test_id("cohort-go-to-triage").click()
            page.wait_for_url(f"{live_app}/cohort/triage")
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright cohort overview flow failed: {exc}")


def test_e2e_groups_drag_distribute_and_suggest(live_app):
    """P2: Director can auto-distribute, request orchestration suggestions,
    and confirm the plan."""
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _seed_role(page, "director", live_app)
            page.goto(f"{live_app}/cohort/groups", wait_until="domcontentloaded")

            # Roster starts populated, groups empty.
            page.wait_for_function(
                "() => Number(document.querySelector('[data-testid=\"roster-count\"]')?.textContent ?? 0) > 0"
            )
            assert page.get_by_test_id("alpha-count").inner_text().strip() == "0"

            # Auto-distribute fills all 3 groups, empties roster.
            page.get_by_test_id("groups-distribute").click()
            page.wait_for_function(
                "() => Number(document.querySelector('[data-testid=\"roster-count\"]')?.textContent ?? 0) === 0"
            )
            for g in ("alpha", "beta", "gamma"):
                count = int(page.get_by_test_id(f"{g}-count").inner_text().strip())
                assert count > 0, f"{g} should have at least one student after auto-distribute"

            # Get suggestions — orchestration returns either suggestions or 'No changes'.
            page.get_by_test_id("groups-suggest").click()
            page.wait_for_function(
                "() => !document.querySelector('[data-testid=\"groups-suggestions\"]')?.hidden"
            )

            # Confirm plan — toast shows.
            page.get_by_test_id("groups-confirm").click()
            page.wait_for_function(
                "() => /Plan confirmed/.test(document.querySelector('[data-testid=\"groups-toast\"]')?.textContent ?? '')"
            )
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright groups flow failed: {exc}")


def test_e2e_invalid_student_id_renders_not_found(live_app):
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _seed_role(page, "director", live_app)
            page.goto(f"{live_app}/students/bogus-id", wait_until="domcontentloaded")
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"profile-not-found\"]') !== null"
            )
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright not-found flow failed: {exc}")


def test_e2e_copilot_answers_grounded_from_live_tools(live_app):
    """The Copilot door: the director opens the panel, clicks a starter
    question, and gets 'Consulted:' pills plus an answer composed from the
    app's real triage/rhythm/journey data (deterministic grounded digest in
    fake-LLM mode — true numbers, not a canned line)."""
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _seed_role(page, "director", live_app)
            page.goto(f"{live_app}/cohort", wait_until="domcontentloaded")

            page.get_by_test_id("copilot-trigger").click()
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"copilot-panel\"]') !== null"
            )
            page.query_selector_all("[data-testid='copilot-starter']")[0].click()

            page.wait_for_function(
                "() => document.querySelectorAll('[data-testid=\"copilot-pill\"]').length >= 3"
            )
            page.wait_for_function(
                "() => /of 24 students/.test(document.querySelector('[data-testid=\"copilot-answer\"]')?.textContent ?? '')"
            )
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright copilot flow failed: {exc}")


def test_e2e_mobile_subnav_docks_to_bottom(live_app):
    """B3 thumb-reach: on a phone viewport the persona subnav is fixed to the
    bottom edge; on desktop it stays in the normal flow."""
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 390, "height": 844})
            _seed_role(page, "seminarian", live_app)
            page.goto(f"{live_app}/me", wait_until="domcontentloaded")
            position = page.evaluate(
                "() => getComputedStyle(document.querySelector('.kc-subnav')).position"
            )
            assert position == "fixed"

            desktop = browser.new_page(viewport={"width": 1440, "height": 900})
            _seed_role(desktop, "seminarian", live_app)
            desktop.goto(f"{live_app}/me", wait_until="domcontentloaded")
            position = desktop.evaluate(
                "() => getComputedStyle(document.querySelector('.kc-subnav')).position"
            )
            assert position == "relative"
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright mobile-subnav flow failed: {exc}")


def test_e2e_formation_year_renders_numbers_and_lines(live_app):
    """C2: the Formation Year page assembles Marcus's record — the numbers
    row fills with his real counts and his reflection lines render."""
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            _seed_role(page, "seminarian", live_app)
            page.goto(f"{live_app}/me/year", wait_until="domcontentloaded")

            # Numbers fill in (Marcus's fixture has 3 reflections).
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"year-stat-reflections\"]')?.textContent === '3'"
            )
            # His reflection lines render as quotes.
            page.wait_for_function(
                "() => [...document.querySelectorAll('[data-testid=\"year-line\"]')]"
                ".some((el) => el.textContent.includes('Led morning prayer'))"
            )
            # The weekly arc renders status words, never raw codes.
            page.wait_for_function(
                "() => /Thriving|Steady|Needs check-in/.test(document.querySelector('[data-testid=\"year-arc\"]')?.textContent ?? '')"
            )
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright formation-year flow failed: {exc}")


def test_e2e_first_run_tour_steps_and_persists_dismissal(live_app):
    """First visit to /me shows the three-step tour; finishing it persists
    (localStorage kc-tour-me) so a reload doesn't show it again."""
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            # Role seeded, tour NOT dismissed — this is the first-run state.
            page.goto(live_app, wait_until="domcontentloaded")
            page.evaluate(
                "() => { localStorage.setItem('kc-role', 'seminarian');"
                " localStorage.setItem('kc-student-id', 'stu-marcus-r'); }"
            )
            page.goto(f"{live_app}/me", wait_until="domcontentloaded")

            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"kc-tour\"]') !== null"
            )
            for _ in range(2):
                page.get_by_test_id("kc-tour-next").click()
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"kc-tour-next\"]')?.textContent === 'Done'"
            )
            page.get_by_test_id("kc-tour-next").click()
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"kc-tour\"]') === null"
            )

            page.reload(wait_until="domcontentloaded")
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"me-status-pill\"]') !== null"
            )
            assert page.query_selector("[data-testid='kc-tour']") is None
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright tour flow failed: {exc}")


def test_e2e_door_previews_swap_in_live_data(live_app):
    """A first-time visitor's door cards preview what's behind them with live
    numbers (REC-1 refinement): the seminarian card swaps in the real next
    curriculum step; the director card renders a check-in count."""
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(live_app, wait_until="domcontentloaded")

            page.wait_for_function(
                "() => (document.querySelector('[data-testid=\"door-preview-next-step\"]')?.textContent ?? '')"
                ".startsWith('Your next step:')"
            )
            page.wait_for_function(
                "() => /(\\d+ students? needs? a check-in|No one needs a check-in)/"
                ".test(document.querySelector('[data-testid=\"door-preview-director-count\"]')?.textContent ?? '')"
            )
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright door preview flow failed: {exc}")


def test_e2e_prayer_submit_petition_then_mark_answered(live_app):
    """Prayer ledger story: Marcus brings a petition, then records how it
    was answered — petition card, status pill, and testimony all render."""
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            _seed_role(page, "seminarian", live_app)
            page.goto(f"{live_app}/me/prayer", wait_until="domcontentloaded")

            # Empty ledger shows the witnessed-not-graded empty state.
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"prayer-empty\"]') !== null"
            )

            # Bring a petition.
            page.get_by_test_id("prayer-new-petition").click()
            page.fill("#petition-text", "Steadiness for Thursday's homily practicum.")
            page.get_by_test_id("prayer-modal-save").click()
            page.wait_for_function(
                "() => [...document.querySelectorAll('[data-testid=\"prayer-card\"] .ledger-text')]"
                ".some((el) => el.textContent.includes('homily practicum'))"
            )

            # Mark it answered with a testimony.
            page.get_by_test_id("prayer-mark-answered").click()
            page.fill("#answer-testimony", "Preached without notes. Grace held.")
            page.get_by_test_id("prayer-modal-save").click()
            page.wait_for_function(
                "() => [...document.querySelectorAll('[data-testid=\"prayer-testimony\"]')]"
                ".some((el) => el.textContent.includes('Grace held'))"
            )

            # The answered arc composes the journey: asked · answered, with the
            # one-time reveal class on the freshly answered card.
            page.wait_for_function(
                "() => { const arc = document.querySelector('[data-testid=\"prayer-answered-arc\"]');"
                " return arc !== null && /Asked \\d{4}/.test(arc.textContent)"
                " && /Answered \\d{4}/.test(arc.textContent)"
                " && document.querySelector('.answered-moment') !== null; }"
            )

            # Track record line reflects the resolved petition.
            page.wait_for_function(
                "() => /1 answered/.test(document.querySelector('[data-testid=\"prayer-track-record\"]')?.textContent ?? '')"
            )
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright prayer ledger flow failed: {exc}")


def test_e2e_prayer_weigh_queue_clears_after_judgment(live_app):
    """Prophecy story: a word where Marcus sits on the weighing council
    appears under 'To weigh' and leaves the queue once he judges it."""
    import json
    import urllib.request

    word = {
        "speaker_id": "stu-grace-w",
        "addressed_to": "stu-anna-t",
        "word": "The catechesis you said yes to is the first room of many.",
        "weigher_ids": ["stu-marcus-r", "stu-luca-b", "fd-theresa"],
    }
    req = urllib.request.Request(
        f"{live_app}/api/prophecies",
        data=json.dumps(word).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            _seed_role(page, "seminarian", live_app)
            page.goto(f"{live_app}/me/prayer", wait_until="domcontentloaded")

            # Badge shows at least one word awaiting his discernment.
            page.wait_for_function(
                "() => Number(document.querySelector('[data-testid=\"weigh-count\"]')?.textContent ?? '0') >= 1"
            )
            page.get_by_test_id("prayer-tab-weigh").click()
            page.wait_for_function(
                "() => [...document.querySelectorAll('[data-testid=\"weigh-card\"] .ledger-text')]"
                ".some((el) => el.textContent.includes('first room of many'))"
            )

            page.fill("[data-testid='weigh-card'] textarea", "Matches the yes she already gave.")
            page.get_by_test_id("weigh-confirm").click()

            # The judged word leaves Marcus's queue.
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"weigh-empty\"]') !== null"
            )
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright weighing flow failed: {exc}")
