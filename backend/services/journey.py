"""Time-bounded shared journey (10X plan C4, REC-8; Hallow's "Pray 40").

One cohort-wide 40-day journey: everyone is on the same day, and the day —
not a content list — is the engagement engine. The journey is defined by its
start date (env `KC_JOURNEY_START`, ISO date). By default the demo starts 11
days ago so surfaces show a lived-in "Day 12 of 40".

Stateless by design: the day is derived from the calendar, so there is
nothing to persist and every surface (and agent) computes the same answer.
"""
from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Any

JOURNEY_NAME = "Forty Days of Discernment"
TOTAL_DAYS = 40

# One theme per week of the journey (day 1-7 → first theme, and so on).
WEEKLY_THEMES = (
    "Naming what you carry",
    "Listening before speaking",
    "The work of your hands",
    "Carrying one another",
    "Fidelity in small things",
    "Speaking what you received",
)


def _start_date(today: date) -> date:
    raw = os.getenv("KC_JOURNEY_START")
    if raw:
        try:
            return date.fromisoformat(raw)
        except ValueError:
            pass  # bad env value → fall through to the demo default
    return today - timedelta(days=11)


def current_journey(today: date | None = None) -> dict[str, Any]:
    today = today or date.today()
    start = _start_date(today)
    day = (today - start).days + 1
    completed = day > TOTAL_DAYS
    upcoming = day < 1
    clamped = min(max(day, 1), TOTAL_DAYS)
    return {
        "name": JOURNEY_NAME,
        "start_date": start.isoformat(),
        "total_days": TOTAL_DAYS,
        "day": clamped,
        "theme": WEEKLY_THEMES[min((clamped - 1) // 7, len(WEEKLY_THEMES) - 1)],
        "completed": completed,
        "upcoming": upcoming,
    }
