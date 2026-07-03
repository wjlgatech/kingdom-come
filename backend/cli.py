"""Console entry point: `kingdom-come` (or `uvx kingdom-come`).

Demo-first defaults so one command gives a working, seeded instance —
the same posture as ./run.sh and the shipped deploy configs. Any env var
already set wins; flags win over env.
"""
from __future__ import annotations

import argparse
import os


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

    print(f"Kingdom Come → http://{args.host}:{args.port}  (docs at /docs)")
    uvicorn.run("backend.app:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
