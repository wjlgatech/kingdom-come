"""CSV cohort import (B4): POST /api/cohorts/{id}/import replaces the
in-process roster all-or-nothing; the shipped demo roster restores between
tests via reset_cohort()."""
import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.fixtures import cohort as cohort_fixtures

client = TestClient(app)
COHORT_ID = cohort_fixtures.COHORT_ID

VALID_CSV = (
    "id,name,engagement,reflection_count,calling\n"
    "stu-new-1,Avery North,0.9,4,evangelism\n"
    "stu-new-2,Blessing Okoro,0.4,1,liturgy;pastoral_care\n"
)


@pytest.fixture(autouse=True)
def restore_roster():
    yield
    cohort_fixtures.reset_cohort()


def _post_csv(cohort_id: str, text: str):
    return client.post(
        f"/api/cohorts/{cohort_id}/import",
        content=text.encode("utf-8"),
        headers={"Content-Type": "text/csv"},
    )


def test_import_replaces_roster():
    res = _post_csv(COHORT_ID, VALID_CSV)
    assert res.status_code == 200
    assert res.json() == {"cohort_id": COHORT_ID, "imported": 2}

    students = client.get("/api/students").json()["students"]
    assert [s["id"] for s in students] == ["stu-new-1", "stu-new-2"]
    assert students[1]["calling"] == ["liturgy", "pastoral_care"]
    # Imported students get an empty profile feed, not a 404.
    profile = client.get("/api/students/stu-new-1").json()
    assert profile["reflections"] == []


def test_import_handles_excel_bom():
    res = client.post(
        f"/api/cohorts/{COHORT_ID}/import",
        content=b"\xef\xbb\xbf" + VALID_CSV.encode("utf-8"),
        headers={"Content-Type": "text/csv"},
    )
    assert res.status_code == 200


def test_bad_row_rejects_whole_import():
    bad = VALID_CSV + "stu-new-3,Cato Reyes,1.7,2,mission\n"  # engagement out of range
    res = _post_csv(COHORT_ID, bad)
    assert res.status_code == 400
    assert "row 4" in res.json()["detail"]
    # All-or-nothing: the shipped roster is untouched.
    students = client.get("/api/students").json()["students"]
    assert len(students) == 24
    assert students[0]["id"] == "stu-marcus-r"


def test_missing_column_and_empty_csv_reject():
    res = _post_csv(COHORT_ID, "id,name\nstu-x,Someone\n")
    assert res.status_code == 400
    assert "missing CSV column" in res.json()["detail"]

    res = _post_csv(COHORT_ID, "id,name,engagement,reflection_count,calling\n")
    assert res.status_code == 400


def test_unknown_cohort_is_404():
    assert _post_csv("nope", VALID_CSV).status_code == 404
