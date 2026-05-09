"""Demo cohort fixtures, ported from frontend/cohort_data.js.

Single source of truth for the agent-facing read endpoints (`/students`,
`/students/{id}`, `/cohorts/{id}/outcomes`). The frontend still loads its
own JS copy until the redesign migrates pages to fetch from these endpoints;
keep the two in sync until then.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

DIRECTOR = {
    "id": "fd-theresa",
    "name": "Sister Theresa Marquez",
    "cohort_id": "st-aloysius-s26",
    "cohort_name": "St. Aloysius cohort, Spring 2026",
}

COHORT_ID = DIRECTOR["cohort_id"]
COHORT_NAME = DIRECTOR["cohort_name"]


def _student(
    sid: str,
    name: str,
    engagement: float,
    reflection_count: int,
    calling: list[str],
    reason_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "id": sid,
        "name": name,
        "cohort_id": COHORT_ID,
        "engagement": engagement,
        "reflection_count": reflection_count,
        "calling": calling,
    }
    if reason_overrides:
        record["reason_overrides"] = reason_overrides
    return record


COHORT: list[dict[str, Any]] = [
    _student("stu-marcus-r", "Marcus Reilly",   0.25, 1, ["evangelism"],     {"few_reflections": {"days": 9}}),
    _student("stu-sarah-k",  "Sarah Kim",       0.18, 0, ["liturgy"],         {"calling_drift": {}}),
    _student("stu-david-o",  "David Okafor",    0.28, 3, ["pastoral_care"]),
    _student("stu-anna-t",   "Anna Theroux",    0.85, 4, ["mission"]),
    _student("stu-luca-b",   "Luca Benedict",   0.62, 3, ["mission"]),
    _student("stu-grace-w",  "Grace Winters",   0.71, 3, ["evangelism"]),
    _student("stu-jonas-r",  "Jonas Reuter",    0.58, 2, ["liturgy"]),
    _student("stu-eli-p",    "Eli Patel",       0.66, 3, ["pastoral_care"]),
    _student("stu-noor-h",   "Noor Habib",      0.74, 3, ["mission"]),
    _student("stu-leo-c",    "Leo Castellano",  0.55, 2, ["evangelism"]),
    _student("stu-isabel-m", "Isabel Marín",    0.83, 4, ["liturgy"]),
    _student("stu-pius-n",   "Pius Nwosu",      0.69, 3, ["pastoral_care"]),
    _student("stu-maria-l",  "Maria Lefevre",   0.61, 2, ["mission"]),
    _student("stu-tomas-v",  "Tomás Vega",      0.77, 3, ["evangelism"]),
    _student("stu-rachel-y", "Rachel Yoon",     0.72, 3, ["liturgy"]),
    _student("stu-james-o",  "James O'Neill",   0.68, 3, ["pastoral_care"]),
    _student("stu-clare-d",  "Clare Donovan",   0.59, 2, ["evangelism"]),
    _student("stu-andrew-j", "Andrew Johansson",0.81, 4, ["mission"]),
    _student("stu-bea-s",    "Bea Solano",      0.56, 2, ["liturgy"]),
    _student("stu-malik-a",  "Malik Adekunle",  0.73, 3, ["pastoral_care"]),
    _student("stu-simone-c", "Simone Chen",     0.65, 3, ["mission"]),
    _student("stu-paul-z",   "Paul Zoller",     0.79, 4, ["evangelism"]),
    _student("stu-rosa-i",   "Rosa Iglesias",   0.84, 4, ["liturgy"]),
    _student("stu-finn-h",   "Finn Hartigan",   0.88, 5, ["pastoral_care"]),
]


PROFILE_FIXTURES: dict[str, dict[str, Any]] = {
    "stu-marcus-r": {
        "reflections": [
            {"date": "2026-04-29", "excerpt": "The small group felt heavy this week. Sister Theresa would say to bring it to prayer."},
            {"date": "2026-04-22", "excerpt": "Mission Theology is harder than I thought. I'm not sure I'm reading it the right way."},
            {"date": "2026-04-15", "excerpt": "Led morning prayer for the first time. Hands shaking, but I did it."},
        ],
        "outcomes": [],
        "risk_history": [
            {"week": "Week 1", "status": "thriving"},
            {"week": "Week 2", "status": "thriving"},
            {"week": "Week 3", "status": "steady"},
            {"week": "Week 4", "status": "steady"},
            {"week": "Week 5", "status": "checkin"},
            {"week": "Week 6", "status": "checkin"},
            {"week": "Week 7", "status": "checkin"},
        ],
    },
    "stu-sarah-k": {
        "reflections": [
            {"date": "2026-04-30", "excerpt": "I keep coming back to the question of whether I'm here for the right reasons."},
            {"date": "2026-04-23", "excerpt": "Liturgy class moved me this week. The Eucharist as the source and summit."},
        ],
        "outcomes": [],
        "risk_history": [
            {"week": "Week 1", "status": "thriving"}, {"week": "Week 2", "status": "steady"},
            {"week": "Week 3", "status": "steady"}, {"week": "Week 4", "status": "checkin"},
            {"week": "Week 5", "status": "checkin"}, {"week": "Week 6", "status": "risk"},
            {"week": "Week 7", "status": "risk"},
        ],
    },
    "stu-david-o": {
        "reflections": [
            {"date": "2026-04-28", "excerpt": "Spring break visit home was harder than expected. Father is sick."},
        ],
        "outcomes": [
            {"date": "2026-03-21", "student_id": "stu-david-o", "impact_score": 0.75, "description": "Led the parish youth retreat preparation team.", "effectiveness": "strong"},
        ],
        "risk_history": [
            {"week": "Week 1", "status": "thriving"}, {"week": "Week 2", "status": "thriving"},
            {"week": "Week 3", "status": "steady"}, {"week": "Week 4", "status": "steady"},
            {"week": "Week 5", "status": "steady"}, {"week": "Week 6", "status": "checkin"},
            {"week": "Week 7", "status": "checkin"},
        ],
    },
    "stu-anna-t": {
        "reflections": [
            {"date": "2026-05-01", "excerpt": "The parish council has invited me to lead next month's catechesis. I said yes."},
            {"date": "2026-04-24", "excerpt": "Three days of silent retreat. I needed it more than I knew."},
        ],
        "outcomes": [
            {"date": "2026-04-18", "student_id": "stu-anna-t", "impact_score": 0.86, "description": "Led a supervised neighborhood cohort.", "effectiveness": "strong"},
            {"date": "2026-03-30", "student_id": "stu-anna-t", "impact_score": 0.72, "description": "Coordinated parish soup kitchen volunteers for Holy Week.", "effectiveness": "developing"},
        ],
        "risk_history": [
            {"week": "Week 1", "status": "steady"}, {"week": "Week 2", "status": "thriving"},
            {"week": "Week 3", "status": "thriving"}, {"week": "Week 4", "status": "thriving"},
            {"week": "Week 5", "status": "thriving"}, {"week": "Week 6", "status": "thriving"},
            {"week": "Week 7", "status": "thriving"},
        ],
    },
}


def list_students(cohort_id: str | None = None) -> list[dict[str, Any]]:
    if cohort_id is None or cohort_id == COHORT_ID:
        return [deepcopy(s) for s in COHORT]
    return []


def get_student(student_id: str) -> dict[str, Any] | None:
    for s in COHORT:
        if s["id"] == student_id:
            base = deepcopy(s)
            profile = PROFILE_FIXTURES.get(student_id, {"reflections": [], "outcomes": [], "risk_history": []})
            base["reflections"] = deepcopy(profile["reflections"])
            base["outcomes"] = deepcopy(profile["outcomes"])
            base["risk_history"] = deepcopy(profile["risk_history"])
            return base
    return None


def list_cohort_outcomes(cohort_id: str) -> list[dict[str, Any]] | None:
    if cohort_id != COHORT_ID:
        return None
    rows: list[dict[str, Any]] = []
    for sid, profile in PROFILE_FIXTURES.items():
        for o in profile["outcomes"]:
            entry = deepcopy(o)
            entry.setdefault("student_id", sid)
            rows.append(entry)
    rows.sort(key=lambda r: r.get("date", ""), reverse=True)
    return rows


def cohort_meta(cohort_id: str) -> dict[str, Any] | None:
    if cohort_id != COHORT_ID:
        return None
    return {
        "id": COHORT_ID,
        "name": COHORT_NAME,
        "director": deepcopy(DIRECTOR),
        "student_count": len(COHORT),
    }
