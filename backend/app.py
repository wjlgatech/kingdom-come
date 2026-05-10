from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from backend.api.ws_chat import router as ws_chat_router
from backend.fixtures import cohort as cohort_fixtures
from backend.services import prayer as prayer_service
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
    {"href": "/me/timeline", "label": "Arc", "key": "arc"},
]
DIRECTOR_SUBNAV = [
    {"href": "/cohort", "label": "Cohort", "key": "cohort"},
    {"href": "/cohort/triage", "label": "Triage", "key": "triage"},
    {"href": "/cohort/groups", "label": "Groups", "key": "groups"},
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


@app.get("/me/timeline", include_in_schema=False)
def timeline_page(request: Request):
    return templates.TemplateResponse(
        request,
        "timeline.html",
        {"subnav": _seminarian_subnav("arc"), "required_role": "seminarian"},
    )


@app.get("/cohort", include_in_schema=False)
def cohort_overview_page(request: Request):
    return templates.TemplateResponse(
        request,
        "cohort_overview.html",
        {"subnav": _director_subnav("cohort"), "required_role": "director"},
    )


@app.get("/cohort/triage", include_in_schema=False)
def triage_page(request: Request):
    return templates.TemplateResponse(
        request,
        "cohort_triage.html",
        {"subnav": _director_subnav("triage"), "required_role": "director"},
    )


@app.get("/cohort/groups", include_in_schema=False)
def cohort_groups_page(request: Request):
    return templates.TemplateResponse(
        request,
        "cohort_groups.html",
        {"subnav": _director_subnav("groups"), "required_role": "director"},
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


# Agent-facing JSON read endpoints. Namespaced under /api so they don't
# collide with the Jinja page routes at /students/{id} and /cohort.
@app.get("/api/students")
def list_students(cohort_id: str | None = None) -> dict[str, list[dict[str, object]]]:
    return {"students": cohort_fixtures.list_students(cohort_id)}


@app.get("/api/students/{student_id}")
def get_student(student_id: str) -> dict[str, object]:
    student = cohort_fixtures.get_student(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail=f"student {student_id} not found")
    return student


@app.get("/api/cohorts/{cohort_id}")
def get_cohort(cohort_id: str) -> dict[str, object]:
    meta = cohort_fixtures.cohort_meta(cohort_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"cohort {cohort_id} not found")
    return meta


@app.get("/api/cohorts/{cohort_id}/outcomes")
def list_cohort_outcomes(cohort_id: str) -> dict[str, list[dict[str, object]]]:
    outcomes = cohort_fixtures.list_cohort_outcomes(cohort_id)
    if outcomes is None:
        raise HTTPException(status_code=404, detail=f"cohort {cohort_id} not found")
    return {"outcomes": outcomes}


# Prayer + prophecy ledgers. Track records for both. See backend/services/prayer.py.
class PrayerRequestIn(BaseModel):
    student_id: str = Field(min_length=1)
    petition: str = Field(min_length=1)
    visibility: str = "small_group"
    recipient_ids: list[str] = Field(default_factory=list)
    scripture: str | None = None


class PrayerAnswerIn(BaseModel):
    status: str
    testimony: str = Field(min_length=1)
    witnesses: list[str] = Field(default_factory=list)


class IntercessionIn(BaseModel):
    peer_id: str = Field(min_length=1)
    message: str = ""


class ProphecyIn(BaseModel):
    speaker_id: str = Field(min_length=1)
    addressed_to: str = Field(min_length=1)
    word: str = Field(min_length=1)
    weigher_ids: list[str]
    visibility: str = "small_group"


class WeighingIn(BaseModel):
    weigher_id: str = Field(min_length=1)
    judgment: str
    notes: str = ""


class FulfillmentIn(BaseModel):
    status: str
    testimony: str = ""
    witnesses: list[str] = Field(default_factory=list)


class CohortPolicyIn(BaseModel):
    tradition: str


def _serialize(obj) -> dict:
    return prayer_service.to_dict(obj)


@app.post("/api/prayer/requests")
def submit_prayer_request(body: PrayerRequestIn) -> dict[str, object]:
    try:
        pr = prayer_service.submit_prayer(
            student_id=body.student_id,
            petition=body.petition,
            visibility=body.visibility,
            recipient_ids=body.recipient_ids,
            scripture=body.scripture,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _serialize(pr)


@app.get("/api/prayer/requests")
def list_prayer_requests(
    student_id: str | None = None,
    status: str | None = None,
    visible_to: str | None = None,
) -> dict[str, list[dict]]:
    rows = prayer_service.list_prayers(
        student_id=student_id, status=status, visible_to=visible_to
    )
    return {"prayers": [_serialize(r) for r in rows]}


@app.get("/api/prayer/requests/{prayer_id}")
def get_prayer_request(prayer_id: str) -> dict[str, object]:
    try:
        pr = prayer_service.get_prayer(prayer_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    intercessions = prayer_service.list_intercessions(prayer_id)
    return {**_serialize(pr), "intercessions": [_serialize(i) for i in intercessions]}


@app.post("/api/prayer/requests/{prayer_id}/watch")
def start_watching_prayer(prayer_id: str) -> dict[str, object]:
    try:
        pr = prayer_service.watch_prayer(prayer_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _serialize(pr)


@app.post("/api/prayer/requests/{prayer_id}/answer")
def answer_prayer_request(prayer_id: str, body: PrayerAnswerIn) -> dict[str, object]:
    try:
        pr = prayer_service.mark_answered(
            prayer_id,
            status=body.status,
            testimony=body.testimony,
            witnesses=body.witnesses,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _serialize(pr)


@app.post("/api/prayer/requests/{prayer_id}/intercessions")
def add_prayer_intercession(prayer_id: str, body: IntercessionIn) -> dict[str, object]:
    try:
        intercession = prayer_service.add_intercession(prayer_id, body.peer_id, body.message)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _serialize(intercession)


@app.post("/api/prophecies")
def submit_prophecy(body: ProphecyIn) -> dict[str, object]:
    try:
        p = prayer_service.submit_prophecy(
            speaker_id=body.speaker_id,
            addressed_to=body.addressed_to,
            word=body.word,
            weigher_ids=body.weigher_ids,
            visibility=body.visibility,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _serialize(p)


@app.get("/api/prophecies")
def list_prophecies(
    speaker_id: str | None = None,
    addressed_to: str | None = None,
    status: str | None = None,
    visible_to: str | None = None,
) -> dict[str, list[dict]]:
    rows = prayer_service.list_prophecies(
        speaker_id=speaker_id,
        addressed_to=addressed_to,
        status=status,
        visible_to=visible_to,
    )
    return {"prophecies": [_serialize(r) for r in rows]}


@app.get("/api/prophecies/{prophecy_id}")
def get_prophecy(prophecy_id: str) -> dict[str, object]:
    try:
        return _serialize(prayer_service.get_prophecy(prophecy_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/prophecies/{prophecy_id}/weighings")
def weigh_prophecy(prophecy_id: str, body: WeighingIn) -> dict[str, object]:
    try:
        p = prayer_service.weigh_prophecy(
            prophecy_id,
            weigher_id=body.weigher_id,
            judgment=body.judgment,
            notes=body.notes,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _serialize(p)


@app.post("/api/prophecies/{prophecy_id}/fulfillment")
def record_prophecy_fulfillment(prophecy_id: str, body: FulfillmentIn) -> dict[str, object]:
    try:
        p = prayer_service.record_fulfillment(
            prophecy_id,
            status=body.status,
            testimony=body.testimony,
            witnesses=body.witnesses,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _serialize(p)


@app.get("/api/prayer/track-record/{student_id}")
def get_prayer_track_record(student_id: str) -> dict[str, object]:
    return {
        "prayer": prayer_service.prayer_track_record(student_id),
        "prophecy": prayer_service.prophecy_track_record(student_id),
    }


@app.get("/api/cohorts/{cohort_id}/prayer-rhythm")
def get_cohort_prayer_rhythm(cohort_id: str) -> dict[str, object]:
    students = cohort_fixtures.list_students(cohort_id)
    if not students:
        raise HTTPException(status_code=404, detail=f"cohort {cohort_id} not found")
    rhythm = prayer_service.cohort_rhythm(s["id"] for s in students)
    return {"cohort_id": cohort_id, "rhythm": rhythm}


@app.get("/api/cohorts/{cohort_id}/policy")
def get_cohort_policy(cohort_id: str) -> dict[str, object]:
    return _serialize(prayer_service.get_policy(cohort_id))


@app.put("/api/cohorts/{cohort_id}/policy")
def set_cohort_policy(cohort_id: str, body: CohortPolicyIn) -> dict[str, object]:
    try:
        return _serialize(prayer_service.set_policy(cohort_id, body.tradition))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
