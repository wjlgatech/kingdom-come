from __future__ import annotations

from .realtime import publish_event


def process_events(student_id: str, message: str = "") -> int:
    return publish_event(
        "activity",
        {"student_id": student_id, "message": message[:200]},
    )
