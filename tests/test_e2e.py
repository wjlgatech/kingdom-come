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
        "LLM_FAKE_RESPONSE": "Peace be with you on this formation journey.",
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


def test_e2e_formation_dashboard_common_and_edge_cases(live_app):
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.goto(f"{live_app}/admin/workbench", wait_until="networkidle")

            assert page.get_by_role("heading", name="Kingdom Come").is_visible()
            page.get_by_label("Engagement").fill("0.18")
            page.get_by_label("Reflections").fill("1")
            page.get_by_role("button", name="Assess risk").click()
            page.wait_for_function(
                "() => /high/i.test(document.querySelector('[data-testid=\"risk-result\"]').innerText)"
            )
            assert "high" in page.get_by_test_id("risk-result").inner_text().lower()

            page.get_by_label("Calling").fill("evangelism")
            page.get_by_role("button", name="Recommend path").click()
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"curriculum-result\"]').innerText.includes('mission_theology')"
            )
            assert "mission_theology" in page.get_by_test_id("curriculum-result").inner_text()

            page.get_by_label("Groups").fill("alpha: Ana, Bo\nbeta: Cy, Dee, Eli")
            page.get_by_role("button", name="Plan class").click()
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"orchestration-result\"]').innerText.includes('merge_group')"
            )
            assert "merge_group" in page.get_by_test_id("orchestration-result").inner_text()

            outcome_form = page.locator("#outcome-form")
            outcome_form.get_by_label("Student ID").fill("stu-7")
            outcome_form.get_by_label("Impact score").fill("0.86")
            outcome_form.get_by_label("Outcome description").fill("Led a supervised neighborhood cohort.")
            page.get_by_role("button", name="Track outcome").click()
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"outcome-result\"]').innerText.includes('strong')"
            )
            assert "stu-7" in page.get_by_test_id("outcome-result").inner_text()

            page.get_by_label("Engagement").fill("1.4")
            page.get_by_role("button", name="Assess risk").click()
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"risk-result\"]').innerText.includes('must be between 0 and 1')"
            )
            assert "must be between 0 and 1" in page.get_by_test_id("risk-result").inner_text()

            page.set_viewport_size({"width": 390, "height": 900})
            assert page.get_by_role("button", name="Assess risk").is_visible()
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright browser flow failed: {exc}")


def test_e2e_chat_flow_for_student_and_professor(live_app):
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.goto(f"{live_app}/admin/workbench", wait_until="networkidle")

            # Student perspective: send a message and see a streaming reply.
            chat_student = page.locator("#chat-student-id")
            chat_student.wait_for()
            chat_student.fill("stu-student")
            chat_message = page.locator("#chat-message")
            chat_message.fill("How am I progressing in evangelism?")
            page.get_by_role("button", name="Send").click()
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"chat-status\"]').innerText === 'ready'"
            )
            assert "Peace be with you" in page.get_by_test_id("chat-result").inner_text()

            # Edge case: empty message surfaces an error without closing the socket.
            chat_message.fill("")
            page.get_by_role("button", name="Send").click()
            page.wait_for_function(
                "() => /required/.test(document.querySelector('[data-testid=\"chat-result\"]').innerText)"
            )
            assert "required" in page.get_by_test_id("chat-result").inner_text()

            # Professor perspective: switch student and continue the same socket.
            chat_student.fill("stu-prof-watch")
            chat_message.fill("Summarize this cohort's spiritual posture.")
            page.get_by_role("button", name="Send").click()
            page.wait_for_function(
                "() => /Peace be with you/.test(document.querySelector('[data-testid=\"chat-result\"]').innerText)"
            )
            assert "Peace be with you" in page.get_by_test_id("chat-result").inner_text()

            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright chat flow failed: {exc}")
