"""Brand conformance, asserted in a real browser (agentic-webapp playbook).

Reading the CSS is not enough: the brand lives in *computed* styles, after the
cascade has resolved `tokens.css` (which still carries a legacy
`prefers-color-scheme: dark` block) against `anthropic-theme.css`. This suite
pins the resolved result on both a light- and a dark-preference machine, so the
warm ivory ground can't be silently flipped by a visitor's OS setting.

Fixtures follow tests/test_e2e_kc.py; assertions read computed style, never a
stylesheet.
"""

import os
import socket
import pathlib
import subprocess
import tempfile
import sys
import time

import pytest
from playwright.sync_api import Error, sync_playwright

# The brand ground, as rgb() — what getComputedStyle actually returns.
IVORY = "rgb(250, 249, 245)"
INK = "rgb(20, 20, 19)"
OFF_BRAND_ACCENTS = {"#7c2d3a", "#d08fa0", "#faf7f2", "#181614"}

# The door (/) is checked separately: with a role in localStorage it redirects,
# so it needs a fresh context and a settled navigation before reading styles.
PAGES = ["/me", "/me/chat", "/me/prayer", "/cohort"]


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
    env.pop("KC_DEMO_SEED", None)
    log = tempfile.NamedTemporaryFile(
        mode="w", suffix=f"-uvicorn-{port}.log", delete=False
    )
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app:app",
         "--host", "127.0.0.1", "--port", str(port)],
        # NOT subprocess.PIPE — an unread pipe fills and blocks the server.
        # See tests/test_e2e_kc.py for the full story.
        stdout=log, stderr=subprocess.STDOUT, text=True, env=env,
    )
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                break
        time.sleep(0.1)
    else:
        log.flush()
        output = pathlib.Path(log.name).read_text()
        process.terminate()
        raise RuntimeError(f"Uvicorn did not start: {output}")

    yield f"http://127.0.0.1:{port}"

    process.terminate()
    process.wait(timeout=5)
    log.close()


def _seed_role(page, base):
    page.goto(base, wait_until="domcontentloaded")
    page.evaluate(
        "() => { localStorage.setItem('kc-role', 'director');"
        " localStorage.setItem('kc-student-id', 'stu-marcus-r');"
        " localStorage.setItem('kc-tour-me', 'done');"
        " localStorage.setItem('kc-tour-cohort', 'done'); }"
    )


@pytest.fixture(scope="module")
def browser():
    """Skip ONLY when the browser genuinely can't launch.

    Everything after launch is a real assertion: a Playwright error mid-test is
    a failure, not a skip. Swallowing those was how this file first reported a
    fake green.
    """
    with sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Error as exc:
            pytest.skip(f"Playwright chromium unavailable: {exc}")
        yield b
        b.close()


def _computed(page):
    return page.evaluate(
        """() => {
            const cs = getComputedStyle(document.body);
            return {
                bg: cs.backgroundColor,
                color: cs.color,
                font: cs.fontFamily,
                accent: cs.getPropertyValue('--accent').trim().toLowerCase(),
            };
        }"""
    )


def _assert_on_brand(computed, where, scheme):
    assert computed["bg"] == IVORY, (
        f"{where} under prefers-color-scheme:{scheme} rendered "
        f"{computed['bg']}, expected brand ivory {IVORY}"
    )
    assert computed["color"] == INK, f"{where} ink drifted: {computed['color']}"
    assert "Poppins" in computed["font"], f"{where} is not on Poppins: {computed['font']}"
    assert computed["accent"] not in OFF_BRAND_ACCENTS, (
        f"{where} fell back to the pre-brand accent {computed['accent']}"
    )


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_e2e_brand_ground_survives_the_os_color_scheme(live_app, browser, scheme):
    """Ivory on both schemes.

    `tokens.css` keeps a dark palette under `prefers-color-scheme: dark`.
    `body[data-theme="anthropic"]` is meant to out-specify it. This test is the
    only thing standing between that assumption and a visitor on a dark-mode
    Mac seeing a pink-accented charcoal app.
    """
    ctx = browser.new_context(color_scheme=scheme)
    try:
        page = ctx.new_page()
        _seed_role(page, live_app)
        for path in PAGES:
            page.goto(live_app + path, wait_until="domcontentloaded")
            _assert_on_brand(_computed(page), path, scheme)
    finally:
        ctx.close()


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_e2e_door_is_on_brand_for_a_first_time_visitor(live_app, browser, scheme):
    """The door is the first thing anyone sees — and the only unseeded surface.

    A fresh context (no kc-role) means no redirect, so styles can be read
    without racing door.js.
    """
    ctx = browser.new_context(color_scheme=scheme)
    try:
        page = ctx.new_page()
        page.goto(live_app + "/", wait_until="networkidle")
        _assert_on_brand(_computed(page), "/ (door)", scheme)
    finally:
        ctx.close()


def test_e2e_no_console_errors_on_primary_surfaces(live_app, browser):
    """Playbook: verify in a real browser — screenshot AND zero console errors."""
    ctx = browser.new_context()
    try:
        page = ctx.new_page()
        problems: list[str] = []
        page.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
        page.on(
            "console",
            lambda m: problems.append(f"console.error: {m.text}")
            if m.type == "error" else None,
        )
        _seed_role(page, live_app)
        for path in PAGES:
            page.goto(live_app + path, wait_until="networkidle")
        assert not problems, "console/page errors on primary surfaces:\n" + "\n".join(problems)
    finally:
        ctx.close()
