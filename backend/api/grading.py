"""Review API for AI-drafted report grades (docs/GRADING.md, M2).

The finalize endpoint is THE human gate: nothing is official until the
professor clicks it. Regenerate is the agentic loop — the professor gives
guidance in their own words and the agent redrafts under it. The batch
endpoint makes the whole workflow CLI-free: the professor drafts new
submissions with one button.
"""

from __future__ import annotations

import threading

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from backend.grading import intake, store, synthesis
from backend.grading.corpus import load_corpus
from backend.grading.extract import SUPPORTED_SUFFIXES, extract_text, parse_student_name
from backend.grading.grader import draft_grade, load_voice_profile

router = APIRouter(prefix="/api/grading", tags=["grading"])

# One drafting job at a time; state is read by the UI's polling loop. In-memory
# is fine: this is a single-professor tool, and drafts land on disk as they finish.
_batch_job: dict = {"running": False, "total": 0, "done": 0, "current": "", "errors": {}}
_batch_lock = threading.Lock()


def _pending_reports() -> list:
    reports = store.reports_dir()
    if not reports.is_dir():
        return []
    pending = []
    for f in sorted(reports.iterdir()):
        if f.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        if (reports / f"{f.stem}.optout").exists():
            continue  # student declined AI grading — manual path
        if (store.drafts_dir() / f"{f.stem}.json").exists():
            continue  # already drafted
        pending.append(f)
    return pending


def _run_batch_job(files: list) -> None:
    profile = load_voice_profile()
    exemplars = load_corpus()
    for f in files:
        _batch_job["current"] = parse_student_name(f)
        try:
            draft = draft_grade(
                parse_student_name(f), extract_text(f), profile=profile, exemplars=exemplars
            )
            data = draft.model_dump()
            data["status"] = "draft"
            store.save_draft(f.stem, data)
        except Exception as exc:  # record and keep going — one bad PDF never stops the run
            _batch_job["errors"][f.name] = str(exc)
        _batch_job["done"] += 1
    _batch_job["current"] = ""
    _batch_job["running"] = False


@router.post("/batch")
def start_batch() -> dict:
    """Draft every new submission (skips opt-outs and already-drafted reports)."""
    with _batch_lock:
        if _batch_job["running"]:
            raise HTTPException(status_code=409, detail="起草任务正在进行中")
        pending = _pending_reports()
        if not pending:
            raise HTTPException(status_code=409, detail="没有待起草的新报告")
        _batch_job.update(running=True, total=len(pending), done=0, current="", errors={})
    threading.Thread(target=_run_batch_job, args=(pending,), daemon=True).start()
    return {"started": len(pending)}


@router.get("/batch/status")
def batch_status() -> dict:
    return dict(_batch_job)


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


@router.post("/synthesis")
def run_synthesis() -> dict:
    """M3: finalized reports -> formation signals -> demand/supply advisory."""
    try:
        return synthesis.run_synthesis()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"synthesis failed: {exc}")


@router.get("/synthesis")
def get_synthesis() -> dict:
    result = synthesis.latest_synthesis()
    if result is None:
        raise HTTPException(status_code=404, detail="no synthesis yet — run one first")
    return result


@router.post("/submissions")
async def submit_report(
    file: UploadFile = File(...), consent: str = Form("")
) -> dict:
    """M4: student upload. Consent is explicit; opt-outs are accepted and
    marked for manual grading (never silently AI-processed)."""
    content = await file.read()
    try:
        return intake.save_submission(file.filename or "", content, consent == "yes")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/submissions")
def submissions() -> dict:
    return {"submissions": intake.list_submissions(), "deadline": intake.deadline().isoformat()}


@router.get("/export.csv")
def export_csv() -> Response:
    return Response(
        content=store.export_gradebook_csv(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=gradebook.csv"},
    )
