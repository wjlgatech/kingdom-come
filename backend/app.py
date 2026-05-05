from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.services.curriculum import recommend_content
from backend.services.orchestration import class_orchestrator
from backend.services.predictive import dropout_risk


app = FastAPI(title="Seminary Formation Platform V7", version="0.7.0")


class StudentSignalRequest(BaseModel):
    engagement: float | None = Field(default=None, ge=0, le=1)
    reflection_count: int | None = Field(default=None, ge=0)
    calling: str | list[str] | None = None
    completed_content: list[str] = Field(default_factory=list)


class GroupRequest(BaseModel):
    id: str
    members: list[str] = Field(default_factory=list)


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
