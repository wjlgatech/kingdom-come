"""Accessibility audit (10X plan B6): axe-core (vendored, offline-safe) runs
against every primary surface; serious/critical WCAG 2.0/2.1 A+AA violations
fail the build. Uses the same live-uvicorn fixture pattern as the E2E suites.
"""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

try:
    from playwright.sync_api import sync_playwright, Error
except ImportError:  # pragma: no cover
    pytest.skip("playwright not installed", allow_module_level=True)

AXE_JS = (Path(__file__).parent / "vendor" / "axe.min.js").read_text()

PAGES = [
    ("/", None),
    ("/me", "seminarian"),
    ("/me/chat", "seminarian"),
    ("/me/prayer", "seminarian"),
    ("/me/timeline", "seminarian"),
    ("/me/year", "seminarian"),
    ("/cohort", "director"),
    ("/cohort/triage", "director"),
    ("/cohort/groups", "director"),
    ("/students/stu-marcus-r", "director"),
]


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def live_app():
    port = _free_port()
    env = os.environ.copy()
    env["EMBEDDING_FAKE"] = "1"
    env["LLM_FAKE_RESPONSE"] = "Walk gently into this week."
    env.pop("REDIS_URL", None)
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app:app", "--port", str(port)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.1)
    yield base
    proc.terminate()
    proc.wait(timeout=10)


def _seed_role(page, role, base):
    page.goto(base, wait_until="domcontentloaded")
    sid = "stu-marcus-r" if role == "seminarian" else "fd-theresa"
    page.evaluate(
        f"() => {{ localStorage.setItem('kc-role', '{role}');"
        f" localStorage.setItem('kc-student-id', '{sid}');"
        " localStorage.setItem('kc-tour-me', 'done');"
        " localStorage.setItem('kc-tour-cohort', 'done'); }"
    )


def test_primary_surfaces_have_no_serious_axe_violations(live_app):
    failures: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            for path, role in PAGES:
                # Fresh context per surface: the door page redirects when a
                # role is already in localStorage, which would tear down the
                # evaluate context mid-seed.
                context = browser.new_context(viewport={"width": 1440, "height": 1000})
                page = context.new_page()
                if role:
                    _seed_role(page, role, live_app)
                page.goto(f"{live_app}{path}", wait_until="networkidle")
                page.evaluate(AXE_JS)
                result = page.evaluate(
                    "() => axe.run(document, {runOnly: {type: 'tag',"
                    " values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']}})"
                )
                serious = [
                    v for v in result["violations"] if v["impact"] in ("serious", "critical")
                ]
                for v in serious:
                    targets = "; ".join(
                        ",".join(n["target"]) for n in v["nodes"][:3]
                    )
                    failures.append(f"{path}: [{v['impact']}] {v['id']} — {v['help']} ({targets})")
                context.close()
            browser.close()
    except Error as exc:
        pytest.fail(f"Playwright a11y run failed: {exc}")

    assert not failures, "axe violations:\n" + "\n".join(failures)
