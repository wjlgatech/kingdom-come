"""1-click activation gates (agentic-webapp playbook).

These are drift tests, not feature tests. They exist because the demo entry
points are exactly the kind of thing that rots silently: a README link keeps
rendering after the deploy behind it goes stale, and nothing fails. Each test
below turns one "someone will notice eventually" into a build failure.

The live-deploy check is opt-in (KC_CHECK_LIVE=1, or `make brand-verify`) so
the default suite stays hermetic and offline.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from backend.cli import DEMO_URL, VERCEL_PROJECT

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"

# The playbook's brand ground. If these change, they change here first.
BRAND_IVORY = "#faf9f5"
BRAND_THEME_ATTR = 'data-theme="anthropic"'


def test_vercel_is_wired_to_serve_the_whole_app():
    """DEMO_URL can't point somewhere we don't actually deploy."""
    assert DEMO_URL == f"https://{VERCEL_PROJECT}.vercel.app"

    cfg = json.loads((ROOT / "vercel.json").read_text())
    assert "api/index.py" in cfg["functions"], "vercel.json must build api/index.py"
    # Every path — Jinja pages, /api/*, /static/* — goes to the one function.
    assert any(r["destination"] == "/api/index" and r["source"] == "/(.*)"
               for r in cfg["rewrites"]), "vercel.json must route all paths to the app"

    entry = (ROOT / "api" / "index.py").read_text()
    assert "from backend.app import app" in entry, "the function must serve the real app"


def test_vercel_requirements_cover_the_runtime_deps():
    """Vercel reads requirements.txt, not pyproject — they must not drift.

    A dep added to pyproject but missed here fails at cold start in production,
    long after every local test went green.
    """
    reqs = (ROOT / "requirements.txt").read_text()
    shipped = {
        line.split(">=")[0].split("==")[0].strip().lower()
        for line in reqs.splitlines()
        if line.strip() and not line.startswith("#")
    }
    pyproject = (ROOT / "pyproject.toml").read_text()
    block = re.search(r"^dependencies = \[(.*?)\]", pyproject, re.S | re.M)
    assert block, "pyproject has no [project.dependencies]"
    needed = {
        m.split(">=")[0].split("==")[0].strip().lower()
        for m in re.findall(r'"([^"]+)"', block.group(1))
    }
    # uvicorn is the local server; Vercel supplies its own.
    needed -= {"uvicorn[standard]", "uvicorn"}
    missing = needed - shipped
    assert not missing, f"requirements.txt is missing runtime deps: {sorted(missing)}"
    # realtime.py imports fakeredis whenever REDIS_URL is unset — which is
    # always, on Vercel. Shipping without it is a cold-start ImportError.
    assert "fakeredis" in shipped, "Vercel has no Redis; fakeredis must ship"


def test_readme_links_the_live_demo_above_the_fold():
    """The deployed demo must be on the first screen, not buried in a section.

    Playbook: the demo link sits at the TOP of the README. 'Above the fold' is
    pinned at the first 12 non-empty lines — roughly one terminal screen.
    """
    lines = [ln for ln in README.read_text().splitlines() if ln.strip()]
    head = "\n".join(lines[:12])
    assert DEMO_URL in head, (
        f"{DEMO_URL} must appear in the first 12 non-empty README lines "
        "(1-click activation: the demo link is above the fold)"
    )


def test_readme_demo_link_is_remotely_visitable():
    """A localhost link is not a demo — the 2026-08-01 amendment."""
    lines = [ln for ln in README.read_text().splitlines() if ln.strip()]
    head = "\n".join(lines[:12])
    for dead in ("127.0.0.1", "localhost", "0.0.0.0"):
        assert dead not in head, (
            f"README's above-the-fold demo link points at {dead}; "
            "1-click means REMOTELY visitable"
        )


def test_make_demo_is_the_one_command():
    makefile = (ROOT / "Makefile").read_text()
    assert re.search(r"^demo:", makefile, re.M), "Makefile needs a `demo` target"
    assert "DEFAULT_GOAL := demo" in makefile, "bare `make` should run the demo"


def test_cli_supports_no_open_for_ci():
    """Auto-open must be suppressible, or containers and CI hang on a browser."""
    out = subprocess.run(
        [sys.executable, "-m", "backend.cli", "--help"],
        capture_output=True, text=True, cwd=ROOT, timeout=60,
    )
    assert out.returncode == 0, out.stderr
    assert "--no-open" in out.stdout


def test_auto_open_is_off_in_ci_and_on_by_default(monkeypatch):
    from backend.cli import _should_open

    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("KC_NO_OPEN", raising=False)
    monkeypatch.setattr(os, "name", "nt")  # skip the Linux-display branch
    assert _should_open(False) is True
    assert _should_open(True) is False

    monkeypatch.setenv("CI", "1")
    assert _should_open(False) is False


def test_pwa_manifest_is_installable_and_on_brand():
    manifest = json.loads((ROOT / "frontend" / "manifest.json").read_text())
    assert manifest["display"] in ("standalone", "fullscreen", "minimal-ui")
    assert manifest["icons"], "an installable PWA needs at least one icon"
    # The hex-hunt has to cover JSON too — a grep over *.css misses this file.
    assert manifest["theme_color"].lower() == BRAND_IVORY
    assert manifest["background_color"].lower() == BRAND_IVORY


def test_base_template_carries_the_brand_theme():
    base = (ROOT / "frontend" / "_base.html").read_text()
    assert BRAND_THEME_ATTR in base, "every page inherits the brand via _base.html"
    assert "anthropic-theme.css" in base
    assert f'content="{BRAND_IVORY}"' in base, "theme-color meta must be brand ivory"


@pytest.mark.skipif(
    not os.getenv("KC_CHECK_LIVE"),
    reason="live-deploy check is opt-in: KC_CHECK_LIVE=1 (or `make brand-verify`)",
)
def test_live_deploy_serves_the_brand_this_repo_ships():
    """Catches the failure that started this: code merged, deploy never ran.

    Green locally + green in CI still means a stale product if nobody pushed
    the image. This asserts against the URL a real visitor opens.
    """
    import urllib.request

    def get(path: str) -> tuple[int, str]:
        req = urllib.request.Request(DEMO_URL + path, headers={"User-Agent": "kc-drift-test"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, ""

    status, _ = get("/static/anthropic-theme.css")
    assert status == 200, (
        f"{DEMO_URL}/static/anthropic-theme.css returned {status} — "
        "the live deploy predates the brand commit. Run `vercel --prod`."
    )

    status, html = get("/me")
    assert status == 200, f"/me returned {status}"
    assert BRAND_THEME_ATTR in html, "live /me is not carrying the brand theme"
    assert f'content="{BRAND_IVORY}"' in html, "live /me theme-color is off-brand"


@pytest.mark.skipif(
    not os.getenv("KC_CHECK_LIVE"),
    reason="live-deploy check is opt-in: KC_CHECK_LIVE=1 (or `make brand-verify`)",
)
def test_live_chat_answers_without_websockets():
    """Vercel has no WebSockets — the demo's mentor must still reply.

    If this fails, /me/chat is a dead surface for every visitor even though
    the WS-based tests pass locally.
    """
    import urllib.request

    body = json.dumps({"student_id": "stu-marcus-r", "message": "How is my week going?"})
    req = urllib.request.Request(
        DEMO_URL + "/api/chat",
        data=body.encode(),
        headers={"Content-Type": "application/json", "User-Agent": "kc-drift-test"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        assert r.status == 200
        data = json.loads(r.read())
    assert not data.get("error"), data["error"]
    assert data.get("reply"), "live /api/chat returned an empty reply"
    assert data.get("done") is True
