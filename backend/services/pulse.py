"""Weekly cohort pulse note (10X plan C5): one short pastoral paragraph for
the director, composed by the mentor LLM chain from counts-only aggregates.

Privacy contract: the prompt receives numbers only — flag counts, prayer
rhythm counts, engagement median. Never ledger content, never names (the
visibility model in `prayer.py` stays intact). With `LLM_FAKE_RESPONSE` set
(tests, keyless demos) the note is the scripted reply, deterministic.
"""
from __future__ import annotations

from statistics import median
from typing import Any

from backend.services.llm_client import stream_llm_response
from backend.services.predictive import dropout_risk


def _flag_counts(students: list[dict[str, Any]]) -> dict[str, int]:
    flagged = 0
    thriving = 0
    for s in students:
        risk = dropout_risk(
            {"engagement": s["engagement"], "reflection_count": s["reflection_count"]}
        )
        # Same weighting the frontend applies (cohort_risk.js): each explicit
        # reason override adds one point if its reason isn't already present.
        extras = [r for r in (s.get("reason_overrides") or {}) if r not in risk["reasons"]]
        score = risk["score"] + len(extras)
        if score >= 2:
            flagged += 1
        elif score == 0:
            thriving += 1
    return {"flagged": flagged, "thriving": thriving, "total": len(students)}


def build_pulse_prompt(students: list[dict[str, Any]], rhythm_rows: list[dict[str, Any]]) -> str:
    counts = _flag_counts(students)
    eng_median = round(median(s["engagement"] for s in students), 2) if students else 0
    totals = {
        "prayers": sum(r.get("prayers_submitted", 0) for r in rhythm_rows),
        "intercessions": sum(r.get("intercessions_offered", 0) for r in rhythm_rows),
        "prophecies": sum(r.get("prophecies_spoken", 0) for r in rhythm_rows),
        "weighings": sum(r.get("weighings_done", 0) for r in rhythm_rows),
    }
    return (
        "You are writing one short note (2-3 sentences, warm but concrete, no "
        "greetings, no bullet points) for a seminary formation director's Monday "
        "morning. Use only these aggregates — you know no names and no content:\n"
        f"- {counts['flagged']} of {counts['total']} students need a check-in; "
        f"{counts['thriving']} are thriving; median engagement {eng_median}.\n"
        f"- Prayer rhythm this season: {totals['prayers']} petitions, "
        f"{totals['intercessions']} intercessions, "
        f"{totals['prophecies']} words with {totals['weighings']} weighings.\n"
        "Name what the week asks of the director, gently."
    )


async def compose_pulse_note(students: list[dict[str, Any]], rhythm_rows: list[dict[str, Any]]) -> str:
    prompt = build_pulse_prompt(students, rhythm_rows)
    chunks = [chunk async for chunk in stream_llm_response(prompt)]
    return "".join(chunks).strip()
