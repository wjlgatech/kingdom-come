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
async def submit_prayer_request(
    student_id: str,
    petition: str,
    visibility: str = "small_group",
    recipient_ids: list[str] | None = None,
    scripture: str | None = None,
) -> str:
    """Submit a prayer request to the prayer ledger. Visibility is one of
    `private` / `small_group` / `cohort`; small_group requires recipient_ids
    (the small-group peers who will pray + intercede). Returns the new
    request including its id (use it to mark answered later)."""
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        r = await client.post(
            f"{_http_base()}/api/prayer/requests",
            json={
                "student_id": student_id,
                "petition": petition,
                "visibility": visibility,
                "recipient_ids": recipient_ids or [],
                "scripture": scripture,
            },
        )
        r.raise_for_status()
        return _format(r.json())


@mcp.tool()
async def list_prayer_requests(
    student_id: str | None = None,
    status: str | None = None,
    visible_to: str | None = None,
) -> str:
    """List prayer requests filtered by student_id / status / visible_to.
    Status is one of `open`, `watching`, `answered_yes`, `partial`, `no`,
    `superseded`. Pass `visible_to` to enforce the visibility policy from a
    given viewer's perspective."""
    params = {k: v for k, v in {
        "student_id": student_id, "status": status, "visible_to": visible_to,
    }.items() if v is not None}
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        r = await client.get(f"{_http_base()}/api/prayer/requests", params=params)
        r.raise_for_status()
        return _format(r.json())


@mcp.tool()
async def mark_prayer_answered(
    prayer_id: str,
    status: str,
    testimony: str,
    witnesses: list[str] | None = None,
) -> str:
    """Mark a prayer request answered. Status is one of `answered_yes`,
    `partial`, `no`, `superseded`. Testimony is required and joins the
    track record."""
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        r = await client.post(
            f"{_http_base()}/api/prayer/requests/{prayer_id}/answer",
            json={"status": status, "testimony": testimony, "witnesses": witnesses or []},
        )
        r.raise_for_status()
        return _format(r.json())


@mcp.tool()
async def add_intercession(prayer_id: str, peer_id: str, message: str = "") -> str:
    """Record that a small-group peer is interceding for a prayer request.
    The message is optional encouragement ("Praying for you, brother")."""
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        r = await client.post(
            f"{_http_base()}/api/prayer/requests/{prayer_id}/intercessions",
            json={"peer_id": peer_id, "message": message},
        )
        r.raise_for_status()
        return _format(r.json())


@mcp.tool()
async def submit_prophecy(
    speaker_id: str,
    addressed_to: str,
    word: str,
    weigher_ids: list[str],
    visibility: str = "small_group",
) -> str:
    """Record a prophetic word. weigher_ids must list 3 distinct weighers
    (2 peers + 1 leader) per the 1 Cor 14:29 weighing rule. The prophecy
    enters status `spoken` and moves to `weighing` once any judgment lands."""
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        r = await client.post(
            f"{_http_base()}/api/prophecies",
            json={
                "speaker_id": speaker_id,
                "addressed_to": addressed_to,
                "word": word,
                "weigher_ids": weigher_ids,
                "visibility": visibility,
            },
        )
        r.raise_for_status()
        return _format(r.json())


@mcp.tool()
async def weigh_prophecy(
    prophecy_id: str,
    weigher_id: str,
    judgment: str,
    notes: str = "",
) -> str:
    """Cast one of the three weighings on a prophecy. Judgment is one of
    `confirm`, `refine`, `reject`. Two confirms lock the status to
    `confirmed`; two rejects to `rejected`; any refine after one judgment
    moves to `refined`."""
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        r = await client.post(
            f"{_http_base()}/api/prophecies/{prophecy_id}/weighings",
            json={"weigher_id": weigher_id, "judgment": judgment, "notes": notes},
        )
        r.raise_for_status()
        return _format(r.json())


@mcp.tool()
async def record_prophecy_fulfillment(
    prophecy_id: str,
    status: str,
    testimony: str,
    witnesses: list[str] | None = None,
) -> str:
    """Record whether a confirmed prophecy was fulfilled. Status is one of
    `pending`, `fulfilled`, `partial`, `unfulfilled`. Testimony is required
    for non-pending status. Only confirmed prophecies accept fulfillment."""
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        r = await client.post(
            f"{_http_base()}/api/prophecies/{prophecy_id}/fulfillment",
            json={"status": status, "testimony": testimony, "witnesses": witnesses or []},
        )
        r.raise_for_status()
        return _format(r.json())


@mcp.tool()
async def list_prophecies(
    speaker_id: str | None = None,
    addressed_to: str | None = None,
    status: str | None = None,
    visible_to: str | None = None,
) -> str:
    """List prophecies filtered by speaker / recipient / status / visibility."""
    params = {k: v for k, v in {
        "speaker_id": speaker_id, "addressed_to": addressed_to,
        "status": status, "visible_to": visible_to,
    }.items() if v is not None}
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        r = await client.get(f"{_http_base()}/api/prophecies", params=params)
        r.raise_for_status()
        return _format(r.json())


@mcp.tool()
async def get_prayer_track_record(student_id: str) -> str:
    """Get a student's track record across both ledgers: prayer answer
    rate + by-status counts; prophecy confirmation rate + fulfillment
    rate + by-status counts. No content (no petitions, no testimonies),
    only counts and rates."""
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        r = await client.get(f"{_http_base()}/api/prayer/track-record/{student_id}")
        r.raise_for_status()
        return _format(r.json())


@mcp.tool()
async def get_cohort_prayer_rhythm(cohort_id: str) -> str:
    """Director-facing aggregate: per-student prayer/prophecy/weighing/
    intercession counts. Counts only — never content. Use this to see who
    has gone quiet spiritually without invading their interior life."""
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        r = await client.get(f"{_http_base()}/api/cohorts/{cohort_id}/prayer-rhythm")
        if r.status_code == 404:
            return _format({"error": "cohort_not_found", "cohort_id": cohort_id})
        r.raise_for_status()
        return _format(r.json())


@mcp.tool()
async def set_cohort_tradition(cohort_id: str, tradition: str) -> str:
    """Set the cohort's tradition policy. Tradition is one of `catholic`
    (lectio + spiritual reading default) or `charismatic` (real-time
    prophetic word default). Same data model serves both; this flag flips
    copy and defaults."""
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        r = await client.put(
            f"{_http_base()}/api/cohorts/{cohort_id}/policy",
            json={"tradition": tradition},
        )
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
