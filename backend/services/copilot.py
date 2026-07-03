"""The in-app Copilot: grounded Q&A over the app's own live data.

The agentic-portfolio pattern applied to Kingdom Come — an on-page agent
that answers a founding user's question from the app's *own tools*, not
from model memory. Architecture is gather-then-ground:

1. Run every tool in the asker's **role scope** (in-process service calls —
   cheap, no HTTP hop) and pack the results as a grounded context.
2. Stream one completion through the mentor's survival chain with the
   question + context, instructed to answer only from the context.
3. With no real model attached (`LLM_FAKE_RESPONSE`, keyless demos, tests),
   compose a deterministic grounded digest from the same tool results — the
   copilot stays *functional*, answering with true numbers, not a canned
   line.

Privacy contract (same as `pulse.py`): the director scope sees names +
statuses + counts, never ledger content; the seminarian scope sees only the
asker's own record. `tests/test_copilot.py` enforces both.
"""
from __future__ import annotations

import os
from statistics import median
from typing import Any, AsyncIterator

from backend.fixtures import cohort as cohort_fixtures
from backend.services import journey as journey_service
from backend.services import prayer as prayer_service
from backend.services.curriculum import recommend_content
from backend.services.llm_client import stream_llm_response
from backend.services.predictive import dropout_risk

# Server-side mirror of frontend/status.js (statusFromRisk + reason
# translations). Keep the two in sync — statuses are words, never scores.
_STATUS_BY_SCORE = ((3, "At risk"), (2, "Needs check-in"), (1, "Steady"), (0, "Thriving"))
_REASON_TEXT = {
    "low_engagement": "engagement has dropped",
    "few_reflections": "hasn't reflected recently",
    "calling_drift": "recent reflections lean away from earlier discernment",
}


def _status_label(score: int) -> str:
    for floor, label in _STATUS_BY_SCORE:
        if score >= floor:
            return label
    return "Thriving"


def _scored_students() -> list[dict[str, Any]]:
    out = []
    for s in cohort_fixtures.list_students():
        risk = dropout_risk(
            {"engagement": s["engagement"], "reflection_count": s["reflection_count"]}
        )
        extras = [r for r in (s.get("reason_overrides") or {}) if r not in risk["reasons"]]
        score = risk["score"] + len(extras)
        reasons = [_REASON_TEXT.get(r, r) for r in risk["reasons"] + extras]
        out.append({"name": s["name"], "status": _status_label(score), "reasons": reasons})
    return out


# ---- role-scoped tools: name -> callable returning a grounded dict ----

def _tool_triage() -> dict[str, Any]:
    students = _scored_students()
    flagged = [s for s in students if s["status"] in ("At risk", "Needs check-in")]
    return {
        "students_total": len(students),
        "needing_attention": [
            {"name": s["name"], "status": s["status"], "why": "; ".join(s["reasons"])}
            for s in flagged
        ],
    }


def _tool_rhythm() -> dict[str, Any]:
    rows = prayer_service.cohort_rhythm(
        s["id"] for s in cohort_fixtures.list_students()
    )
    return {
        "petitions": sum(r["prayers_submitted"] for r in rows),
        "answered": sum(r["prayers_answered"] for r in rows),
        "intercessions": sum(r["intercessions_offered"] for r in rows),
        "words_spoken": sum(r["prophecies_spoken"] for r in rows),
        "weighings_done": sum(r["weighings_done"] for r in rows),
    }


def _tool_engagement() -> dict[str, Any]:
    students = cohort_fixtures.list_students()
    return {"median_engagement": round(median(s["engagement"] for s in students), 2)}


def _tool_journey() -> dict[str, Any]:
    j = journey_service.current_journey()
    return {"journey": j["name"], "day": j["day"], "of": j["total_days"], "theme": j["theme"]}


def _tool_my_status(student_id: str) -> dict[str, Any]:
    s = cohort_fixtures.get_student(student_id)
    if s is None:
        return {}
    risk = dropout_risk(
        {"engagement": s["engagement"], "reflection_count": s["reflection_count"]}
    )
    extras = [r for r in (s.get("reason_overrides") or {}) if r not in risk["reasons"]]
    return {
        "name": s["name"],
        "status": _status_label(risk["score"] + len(extras)),
        "reflections_written": len(s.get("reflections", [])),
        "outcomes_logged": len(s.get("outcomes", [])),
    }


def _tool_my_track_record(student_id: str) -> dict[str, Any]:
    pr = prayer_service.prayer_track_record(student_id)
    ph = prayer_service.prophecy_track_record(student_id)
    return {
        "petitions": pr["total"],
        "answered_favorably": pr["answered_favorable"],
        "words_spoken": ph["total_spoken"],
        "words_confirmed": ph["by_status"].get("confirmed", 0),
    }


def _tool_my_next_steps(student_id: str) -> dict[str, Any]:
    s = cohort_fixtures.get_student(student_id)
    if s is None:
        return {}
    recs = recommend_content({"calling": s["calling"], "completed_content": []})
    return {"next_steps": [r.replace("_", " ") for r in recs[:3]]}


DIRECTOR_TOOLS: dict[str, Any] = {
    "triage": _tool_triage,
    "prayer rhythm": _tool_rhythm,
    "engagement": _tool_engagement,
    "journey": _tool_journey,
}

SEMINARIAN_TOOLS: dict[str, Any] = {
    "my status": _tool_my_status,
    "my track record": _tool_my_track_record,
    "next steps": _tool_my_next_steps,
    "journey": _tool_journey,
}


def gather_context(role: str, student_id: str | None = None) -> dict[str, dict[str, Any]]:
    """Run every tool in the role's scope. Director scope never receives a
    student_id — it cannot reach anyone's ledger content by construction."""
    if role == "director":
        return {name: fn() for name, fn in DIRECTOR_TOOLS.items()}
    if role == "seminarian" and student_id:
        return {
            name: (fn(student_id) if name != "journey" else fn())
            for name, fn in SEMINARIAN_TOOLS.items()
        }
    raise ValueError(f"unknown copilot scope: role={role!r}")


def _grounded_digest(role: str, context: dict[str, dict[str, Any]]) -> str:
    """Deterministic answer used when no real model is attached — composed
    from the same tool results, so the keyless demo answers with true data."""
    if role == "director":
        triage, rhythm = context["triage"], context["prayer rhythm"]
        j = context["journey"]
        flagged = triage["needing_attention"]
        lines = []
        if flagged:
            names = "; ".join(f"{s['name']} ({s['why']})" for s in flagged)
            lines.append(
                f"{len(flagged)} of {triage['students_total']} students would welcome a check-in: {names}."
            )
        else:
            lines.append(f"All {triage['students_total']} students are holding steady.")
        lines.append(
            f"The cohort has brought {rhythm['petitions']} petitions "
            f"({rhythm['answered']} answered), offered {rhythm['intercessions']} intercessions, "
            f"and weighed {rhythm['weighings_done']} of the words spoken."
        )
        lines.append(f"You're on day {j['day']} of {j['of']} of {j['journey']} — this week: {j['theme'].lower()}.")
        return " ".join(lines)

    status, record = context["my status"], context["my track record"]
    steps, j = context["next steps"], context["journey"]
    lines = []
    if status:
        lines.append(
            f"You're {status['status'].lower()} this week, with {status['reflections_written']} "
            f"reflections written and {status['outcomes_logged']} outcomes logged."
        )
    lines.append(
        f"Your ledger holds {record['petitions']} petitions ({record['answered_favorably']} "
        f"answered favorably) and {record['words_spoken']} words spoken "
        f"({record['words_confirmed']} confirmed)."
    )
    if steps.get("next_steps"):
        lines.append(f"Your next step: {steps['next_steps'][0]}.")
    lines.append(f"Day {j['day']} of {j['of']} of {j['journey']} — this week: {j['theme'].lower()}.")
    return " ".join(lines)


def _prompt(role: str, question: str, context: dict[str, dict[str, Any]]) -> str:
    import json

    who = "a seminary formation director" if role == "director" else "a seminarian"
    return (
        f"You are the in-app guide of a formation platform, answering {who}. "
        "Answer the question in 2-4 warm, concrete sentences using ONLY the data "
        "below — if the data doesn't answer it, say what you'd need. Never invent "
        "names or numbers.\n\n"
        f"DATA: {json.dumps(context, ensure_ascii=False)}\n\n"
        f"QUESTION: {question}"
    )


async def answer(role: str, question: str, student_id: str | None = None) -> AsyncIterator[Any]:
    """WS-shaped stream: {'context': [tool names]} first, then text chunks.
    (The endpoint appends {'done': True}; errors surface as {'error': ...} —
    same contract family as handle_chat_ws.)"""
    context = gather_context(role, student_id)
    yield {"context": list(context.keys())}
    if os.getenv("LLM_FAKE_RESPONSE"):
        # No real model: deterministic grounded digest, still true data.
        yield _grounded_digest(role, context)
        return
    async for chunk in stream_llm_response(_prompt(role, question, context)):
        yield chunk
