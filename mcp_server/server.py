"""Kingdom Come MCP server (stdio).

Exposes the running KC FastAPI as MCP tools. Configure via env:
- KC_BASE_URL  (default http://127.0.0.1:8000) — HTTP base for /api and form endpoints
- KC_WS_URL    (default derived from KC_BASE_URL) — WebSocket base for /ws/chat
- KC_TIMEOUT_S (default 30)

Run:
    python -m mcp_server.server

Agent harnesses (Claude Code, Codex, etc.) launch this as a stdio child process.
"""
from __future__ import annotations

import json
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP


def _http_base() -> str:
    return os.getenv("KC_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def _ws_base() -> str:
    explicit = os.getenv("KC_WS_URL")
    if explicit:
        return explicit.rstrip("/")
    base = _http_base()
    if base.startswith("https://"):
        return "wss://" + base[len("https://"):]
    if base.startswith("http://"):
        return "ws://" + base[len("http://"):]
    return base


def _timeout() -> float:
    return float(os.getenv("KC_TIMEOUT_S", "30"))


mcp = FastMCP("kingdom-come")


def _format(payload: Any) -> str:
    """MCP tool results are strings; agents parse the JSON when they need to."""
    return json.dumps(payload, indent=2, ensure_ascii=False)


@mcp.tool()
async def dropout_risk(engagement: float, reflection_count: int) -> str:
    """Score dropout risk for a single student from engagement (0..1) and
    reflection count. Returns score, level, and reason codes."""
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        r = await client.post(
            f"{_http_base()}/predictive/dropout-risk",
            json={"engagement": engagement, "reflection_count": reflection_count},
        )
        r.raise_for_status()
        return _format(r.json())


@mcp.tool()
async def curriculum_recommend(
    calling: str | list[str],
    completed_content: list[str] | None = None,
) -> str:
    """Recommend curriculum content for a student given their calling
    (string or list) and any already-completed content."""
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        r = await client.post(
            f"{_http_base()}/curriculum/recommendations",
            json={"calling": calling, "completed_content": completed_content or []},
        )
        r.raise_for_status()
        return _format(r.json())


@mcp.tool()
async def orchestration_plan(groups: list[dict[str, Any]]) -> str:
    """Generate class orchestration actions for a list of small groups.
    Each group is `{id: str, members: [str, ...]}`. Returns merge/split actions."""
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        r = await client.post(f"{_http_base()}/orchestration/actions", json=groups)
        r.raise_for_status()
        return _format(r.json())


@mcp.tool()
async def log_outcome(student_id: str, impact_score: float, description: str) -> str:
    """Record a ministry outcome for a student. impact_score is 0..1.
    Returns the recorded outcome plus an effectiveness band
    (strong / developing / needs_support)."""
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        r = await client.post(
            f"{_http_base()}/outcomes",
            json={
                "student_id": student_id,
                "impact_score": impact_score,
                "description": description,
            },
        )
        r.raise_for_status()
        return _format(r.json())


@mcp.tool()
async def list_students(cohort_id: str | None = None) -> str:
    """List students. Pass cohort_id to filter; omit for the full roster."""
    params = {"cohort_id": cohort_id} if cohort_id else None
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        r = await client.get(f"{_http_base()}/api/students", params=params)
        r.raise_for_status()
        return _format(r.json())


@mcp.tool()
async def get_student(student_id: str) -> str:
    """Get a single student profile: id, name, calling, engagement,
    reflection_count, plus reflections / outcomes / risk_history history."""
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        r = await client.get(f"{_http_base()}/api/students/{student_id}")
        if r.status_code == 404:
            return _format({"error": "student_not_found", "student_id": student_id})
        r.raise_for_status()
        return _format(r.json())


@mcp.tool()
async def get_cohort(cohort_id: str) -> str:
    """Get cohort metadata: name, director, student_count."""
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        r = await client.get(f"{_http_base()}/api/cohorts/{cohort_id}")
        if r.status_code == 404:
            return _format({"error": "cohort_not_found", "cohort_id": cohort_id})
        r.raise_for_status()
        return _format(r.json())


@mcp.tool()
async def list_cohort_outcomes(cohort_id: str) -> str:
    """List all ministry outcomes recorded for a cohort, newest first."""
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        r = await client.get(f"{_http_base()}/api/cohorts/{cohort_id}/outcomes")
        if r.status_code == 404:
            return _format({"error": "cohort_not_found", "cohort_id": cohort_id})
        r.raise_for_status()
        return _format(r.json())


@mcp.tool()
async def chat_with_mentor(student_id: str, message: str) -> str:
    """Send one message to the AI mentor for `student_id` over the WS chat
    pipeline and return the recalled memory (if any) plus the full response.
    Streaming is collapsed into a single response — the agent gets the whole
    reply, not chunks."""
    from websockets.asyncio.client import connect as ws_connect

    url = f"{_ws_base()}/ws/chat"
    chunks: list[str] = []
    memory: list[str] = []
    error: str | None = None

    async with ws_connect(url, open_timeout=_timeout()) as ws:
        await ws.send(json.dumps({"student_id": student_id, "message": message}))
        while True:
            raw = await ws.recv()
            data = json.loads(raw)
            if "memory" in data:
                memory = data["memory"]
                continue
            if "error" in data:
                error = data["error"]
                break
            if data.get("done"):
                break
            if "chunk" in data:
                chunks.append(data["chunk"])

    return _format({
        "student_id": student_id,
        "memory": memory,
        "response": "".join(chunks).strip(),
        **({"error": error} if error else {}),
    })


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
