"""Review API for AI-drafted report grades (docs/GRADING.md, M2).

The finalize endpoint is THE human gate: nothing is official until the
professor clicks it. Regenerate is the agentic loop — the professor gives
guidance in their own words and the agent redrafts under it.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from backend.grading import store
from backend.grading.corpus import load_corpus
from backend.grading.grader import draft_grade, load_voice_profile

router = APIRouter(prefix="/api/grading", tags=["grading"])


class DraftEdit(BaseModel):
    grade: int | None = None
    comment: str | None = None
    rationale: str | None = None


class RegenerateRequest(BaseModel):
    guidance: str  # the professor's instruction, in their own words


@router.get("/drafts")
def list_drafts() -> dict:
    return {"drafts": store.list_drafts()}


@router.get("/drafts/{draft_id}")
def get_draft(draft_id: str) -> dict:
    try:
        data = store.get_draft(draft_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="draft not found")
    data["report_text"] = store.report_text_for(draft_id)
    return data


@router.put("/drafts/{draft_id}")
def edit_draft(draft_id: str, edit: DraftEdit) -> dict:
    try:
        return store.update_draft(
            draft_id, grade=edit.grade, comment=edit.comment, rationale=edit.rationale
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="draft not found")
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/drafts/{draft_id}/finalize")
def finalize(draft_id: str) -> dict:
    try:
        return store.finalize_draft(draft_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="draft not found")


@router.post("/drafts/{draft_id}/reopen")
def reopen(draft_id: str) -> dict:
    try:
        return store.reopen_draft(draft_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="draft not found")


@router.post("/drafts/{draft_id}/regenerate")
def regenerate(draft_id: str, req: RegenerateRequest) -> dict:
    try:
        current = store.get_draft(draft_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="draft not found")
    if current.get("status") == "final":
        raise HTTPException(status_code=409, detail="draft is finalized — reopen it first")
    report_text = store.report_text_for(draft_id)
    if not report_text:
        raise HTTPException(status_code=409, detail="original report file not found for this draft")
    try:
        redraft = draft_grade(
            current["student"],
            report_text,
            profile=load_voice_profile(),
            exemplars=load_corpus(),
            guidance=req.guidance,
        )
    except Exception as exc:  # LLM/parse failure — keep the current draft intact
        raise HTTPException(status_code=502, detail=f"regenerate failed: {exc}")
    data = redraft.model_dump()
    data["status"] = "draft"
    data["last_guidance"] = req.guidance
    store.save_draft(draft_id, data)
    data["id"] = draft_id
    return data


@router.get("/export.csv")
def export_csv() -> Response:
    return Response(
        content=store.export_gradebook_csv(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=gradebook.csv"},
    )
