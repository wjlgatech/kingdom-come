from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from backend.api.ws_chat import router as ws_chat_router
from backend.services.curriculum import recommend_content
from backend.services.orchestration import class_orchestrator
from backend.services.predictive import dropout_risk


app = FastAPI(title="Seminary Formation Platform V7", version="0.7.0")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
app.include_router(ws_chat_router)

templates = Jinja2Templates(directory=FRONTEND_DIR)


SEMINARIAN_SUBNAV = [
    {"href": "/me", "label": "Today", "key": "today"},
    {"href": "/me/chat", "label": "Mentor", "key": "mentor"},
]
DIRECTOR_SUBNAV = [
    {"href": "/cohort/triage", "label": "Triage", "key": "triage"},
]


def _seminarian_subnav(active_key: str) -> list[dict]:
    return [{**item, "active": item["key"] == active_key} for item in SEMINARIAN_SUBNAV]


def _director_subnav(active_key: str) -> list[dict]:
    return [{**item, "active": item["key"] == active_key} for item in DIRECTOR_SUBNAV]


class StudentSignalRequest(BaseModel):
    engagement: float | None = None
    reflection_count: int | None = None
    calling: str | list[str] | None = None
    completed_content: list[str] = Field(default_factory=list)


class GroupRequest(BaseModel):
    id: str
    members: list[str] = Field(default_factory=list)


class MinistryOutcomeRequest(BaseModel):
    student_id: str = Field(min_length=1)
    impact_score: float = Field(ge=0, le=1)
    description: str = Field(min_length=1)


@app.get("/", include_in_schema=False)
def landing_page(request: Request):
    return templates.TemplateResponse(request, "door.html", {"subnav": None})


@app.get("/me", include_in_schema=False)
def me_page(request: Request):
    return templates.TemplateResponse(
        request,
        "me.html",
        {"subnav": _seminarian_subnav("today"), "required_role": "seminarian"},
    )


@app.get("/me/chat", include_in_schema=False)
def chat_page(request: Request):
    return templates.TemplateResponse(
        request,
        "chat.html",
        {"subnav": _seminarian_subnav("mentor"), "required_role": "seminarian"},
    )


@app.get("/cohort/triage", include_in_schema=False)
def triage_page(request: Request):
    return templates.TemplateResponse(
        request,
        "cohort_triage.html",
        {"subnav": _director_subnav("triage"), "required_role": "director"},
    )


@app.get("/students/{student_id}", include_in_schema=False)
def profile_page(request: Request, student_id: str):
    return templates.TemplateResponse(
        request,
        "student_profile.html",
        {
            "subnav": _director_subnav("triage"),
            "required_role": "director",
            "student_id": student_id,
        },
    )


@app.get("/admin/workbench", include_in_schema=False)
def workbench_page() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "seminary-formation-platform-v7"}


@app.post("/predictive/dropout-risk")
def predictive_dropout_risk(student: StudentSignalRequest) -> dict[str, object]:
    try:
        return dropout_risk(student.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/curriculum/recommendations")
def curriculum_recommendations(student: StudentSignalRequest) -> dict[str, list[str]]:
    return {"recommendations": recommend_content(student.model_dump(exclude_none=True))}


@app.post("/orchestration/actions")
def orchestration_actions(groups: list[GroupRequest]) -> dict[str, list[dict[str, object]]]:
    return {"actions": class_orchestrator([group.model_dump() for group in groups])}


@app.post("/outcomes")
def record_outcome(outcome: MinistryOutcomeRequest) -> dict[str, object]:
    if outcome.impact_score >= 0.75:
        effectiveness = "strong"
    elif outcome.impact_score >= 0.4:
        effectiveness = "developing"
    else:
        effectiveness = "needs_support"

    return {**outcome.model_dump(), "effectiveness": effectiveness}
