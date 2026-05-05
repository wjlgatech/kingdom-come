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
    process = subprocess.Popen(
        ["python", "-m", "uvicorn", "backend.app:app", "--host", "127.0.0.1", "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
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
            page.goto(live_app, wait_until="networkidle")

            assert page.get_by_role("heading", name="Kingdom Come").is_visible()
            page.get_by_label("Engagement").fill("0.18")
            page.get_by_label("Reflections").fill("1")
            page.get_by_role("button", name="Assess risk").click()
            page.get_by_test_id("risk-result").wait_for()
            assert "high" in page.get_by_test_id("risk-result").inner_text().lower()

            page.get_by_label("Calling").fill("evangelism")
            page.get_by_role("button", name="Recommend path").click()
            page.get_by_test_id("curriculum-result").wait_for()
            assert "mission_theology" in page.get_by_test_id("curriculum-result").inner_text()

            page.get_by_label("Groups").fill("alpha: Ana, Bo\nbeta: Cy, Dee, Eli")
            page.get_by_role("button", name="Plan class").click()
            page.wait_for_function(
                "() => document.querySelector('[data-testid=\"orchestration-result\"]').innerText.includes('merge_group')"
            )
            assert "merge_group" in page.get_by_test_id("orchestration-result").inner_text()

            page.get_by_label("Student ID").fill("stu-7")
            page.get_by_label("Impact score").fill("0.86")
            page.get_by_label("Outcome description").fill("Led a supervised neighborhood cohort.")
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
