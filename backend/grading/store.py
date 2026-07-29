"""Draft store for the review surface — a directory, not a database.

Layout (root = $KC_GRADING_DIR, default ./grading_data, gitignored):

    grading_data/
      reports/   student submissions (PDF/txt) — what batch.py reads
      drafts/    one JSON per student — what batch.py writes, this store manages

The batch CLI and the webapp share the same files, so the professor can run
the batch from a terminal and review in the browser with zero import steps.
Draft lifecycle: "draft" -> (edit / regenerate)* -> "final". Finalized drafts
are immutable unless reopened. Draft ids are file stems; sanitized against
path traversal.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .extract import SUPPORTED_SUFFIXES, extract_text


def root_dir() -> Path:
    return Path(os.getenv("KC_GRADING_DIR", "grading_data"))


def reports_dir() -> Path:
    return root_dir() / "reports"


def drafts_dir() -> Path:
    return root_dir() / "drafts"


def _safe_id(draft_id: str) -> str:
    if "/" in draft_id or "\\" in draft_id or draft_id.startswith(".") or not draft_id.strip():
        raise KeyError(draft_id)
    return draft_id


def _draft_path(draft_id: str) -> Path:
    return drafts_dir() / f"{_safe_id(draft_id)}.json"


def list_drafts() -> list[dict]:
    items = []
    if drafts_dir().is_dir():
        for f in sorted(drafts_dir().glob("*.json")):
            if f.name == "summary.json":
                continue
            data = json.loads(f.read_text(encoding="utf-8"))
            items.append(
                {
                    "id": f.stem,
                    "student": data.get("student", f.stem),
                    "grade": data.get("grade"),
                    "status": data.get("status", "draft"),
                    "needs_attention": data.get("needs_attention", False),
                    "flag_notes": data.get("flag_notes", []),
                    "finalized_at": data.get("finalized_at"),
                }
            )
    return items


def get_draft(draft_id: str) -> dict:
    path = _draft_path(draft_id)
    if not path.is_file():
        raise KeyError(draft_id)
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("status", "draft")
    data["id"] = draft_id
    return data


def save_draft(draft_id: str, data: dict) -> None:
    data = {k: v for k, v in data.items() if k != "id"}
    _draft_path(draft_id).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def report_text_for(draft_id: str) -> str | None:
    """The submission text for a draft, matched by file stem."""
    _safe_id(draft_id)
    if reports_dir().is_dir():
        for f in reports_dir().iterdir():
            if f.stem == draft_id and f.suffix.lower() in SUPPORTED_SUFFIXES:
                try:
                    return extract_text(f)
                except Exception:
                    return None
    return None


def update_draft(draft_id: str, grade: int | None = None, comment: str | None = None,
                 rationale: str | None = None) -> dict:
    data = get_draft(draft_id)
    if data["status"] == "final":
        raise PermissionError("draft is finalized — reopen it first")
    if grade is not None:
        data["grade"] = grade
    if comment is not None:
        data["comment"] = comment
    if rationale is not None:
        data["rationale"] = rationale
    data["edited_at"] = datetime.now(timezone.utc).isoformat()
    save_draft(draft_id, data)
    return data


def finalize_draft(draft_id: str) -> dict:
    """THE human gate: only this transition makes a grade/comment official."""
    data = get_draft(draft_id)
    data["status"] = "final"
    data["finalized_at"] = datetime.now(timezone.utc).isoformat()
    save_draft(draft_id, data)
    return data


def reopen_draft(draft_id: str) -> dict:
    data = get_draft(draft_id)
    data["status"] = "draft"
    data["finalized_at"] = None
    save_draft(draft_id, data)
    return data


def export_gradebook_csv() -> str:
    """Finalized rows only — unreviewed drafts never leave the system."""
    import csv
    import io

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["student", "grade", "finalized_at"])
    for item in list_drafts():
        if item["status"] == "final":
            writer.writerow([item["student"], item["grade"], item["finalized_at"]])
    return "﻿" + buf.getvalue()  # BOM so Excel opens Chinese names correctly
