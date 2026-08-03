"""Console entry point: `kingdom-come` (or `uvx kingdom-come`).

Demo-first defaults so one command gives a working, seeded instance —
the same posture as ./run.sh and the shipped deploy configs. Any env var
already set wins; flags win over env.

1-click activation (agentic-webapp playbook): starting the server opens the
browser on the door page. `--no-open` (or KC_NO_OPEN=1) suppresses it for CI,
containers, and headless hosts. `DEMO_URL` is the canonical deployed demo and
is pinned to the README's above-the-fold link by
`tests/test_demo_entry.py` — undemoed means unshipped.
"""
from __future__ import annotations

import argparse
import os
import threading
import urllib.request

# The public, remotely-visitable demo. Vercel is the standard host across the
# whole portfolio, so Kingdom Come deploys there too (vercel.json + api/index.py).
# tests/test_demo_entry.py pins this to the README's above-the-fold link.
VERCEL_PROJECT = "kingdom-come"
DEMO_URL = f"https://{VERCEL_PROJECT}.vercel.app"


def _wait_and_open(url: str, timeout_s: float = 20.0) -> None:
    """Open the browser once the server actually answers.

    Polling /health first avoids the classic race where the tab loads before
    uvicorn binds and the user sees a connection error on a "1-click" launch.
    Every failure path is silent: a headless box must never crash the server.
    """
    import time
    import webbrowser

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=1) as resp:
                if resp.status == 200:
                    break
        except Exception:
            time.sleep(0.25)
    else:
        return
    try:
        webbrowser.open(url)
    except Exception:
        pass


def _should_open(no_open_flag: bool) -> bool:
    """Auto-open unless told not to, or unless there's plainly no display."""
    if no_open_flag or os.getenv("KC_NO_OPEN"):
        return False
    # Common headless signals: CI runners and Linux hosts with no X/Wayland.
    if os.getenv("CI"):
        return False
    if os.name == "posix" and os.uname().sysname == "Linux":
        if not (os.getenv("DISPLAY") or os.getenv("WAYLAND_DISPLAY")):
            return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="kingdom-come",
        description="Kingdom Come — predictive formation intelligence. Serves UI + API.",
    )
    parser.add_argument("--host", default=os.getenv("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    parser.add_argument(
        "--no-demo",
        action="store_true",
        help="start with empty ledgers instead of the seeded demo week",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="don't open a browser on start (CI, containers, headless hosts)",
    )
    args = parser.parse_args()

    if args.no_demo:
        os.environ["KC_DEMO_SEED"] = "0"
    else:
        os.environ.setdefault("KC_DEMO_SEED", "1")
    # With no LLM key at all the mentor still answers (scripted fallback).
    if not any(os.getenv(k) for k in ("NVIDIA_API_KEY", "OPENROUTER_API_KEY", "OPENAI_API_KEY")):
        os.environ.setdefault(
            "LLM_FAKE_RESPONSE",
            "Walk gently into this week. What you named is worth one more honest paragraph.",
        )

    import uvicorn

    # 0.0.0.0 is a bind address, not a browsable one.
    browse_host = "127.0.0.1" if args.host in ("0.0.0.0", "::") else args.host
    local_url = f"http://{browse_host}:{args.port}"

    print(f"Kingdom Come → {local_url}  (docs at /docs)")
    if _should_open(args.no_open):
        print("Opening your browser… (--no-open to skip)")
        threading.Thread(target=_wait_and_open, args=(local_url,), daemon=True).start()

    uvicorn.run("backend.app:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
