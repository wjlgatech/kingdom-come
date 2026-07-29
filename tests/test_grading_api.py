"""Review API tests — TestClient over the real app, LLM faked, tmp data dir."""

import json

import pytest
from fastapi.testclient import TestClient

from backend.app import app

GOOD_REPORT = (
    "我在操练提议中选择了默想与禁食。"
    + "这六周的经历让我学到很多。" * 300
    + "我的退省经历：我去了山上的营地。"
)

FAKE_RESPONSE = json.dumps(
    {"grade": 92, "comment": "王明同学\n谢谢你的报告。\n陈老师", "rationale": "三部分齐全。"},
    ensure_ascii=False,
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("KC_GRADING_DIR", str(tmp_path))
    monkeypatch.setenv("GRADING_FAKE_RESPONSE", FAKE_RESPONSE)
    (tmp_path / "reports").mkdir()
    (tmp_path / "drafts").mkdir()
    (tmp_path / "reports" / "王明_报告.txt").write_text(GOOD_REPORT, encoding="utf-8")
    (tmp_path / "drafts" / "王明_报告.json").write_text(
        json.dumps(
            {
                "student": "王明", "grade": 95, "comment": "初稿评语", "rationale": "初稿依据",
                "flags": [], "flag_notes": [], "needs_attention": False, "status": "draft",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return TestClient(app)


def test_list_and_get_draft(client):
    drafts = client.get("/api/grading/drafts").json()["drafts"]
    assert len(drafts) == 1
    assert drafts[0]["student"] == "王明"

    detail = client.get("/api/grading/drafts/王明_报告").json()
    assert detail["comment"] == "初稿评语"
    assert "退省" in detail["report_text"]


def test_missing_draft_is_404(client):
    assert client.get("/api/grading/drafts/nobody").status_code == 404


def test_path_traversal_is_rejected(client):
    assert client.get("/api/grading/drafts/..%2Fsecrets").status_code in (404, 422)


def test_edit_then_finalize_then_locked(client):
    r = client.put("/api/grading/drafts/王明_报告", json={"grade": 96, "comment": "改过的评语"})
    assert r.status_code == 200 and r.json()["grade"] == 96

    r = client.post("/api/grading/drafts/王明_报告/finalize")
    assert r.json()["status"] == "final"

    # finalized -> edits and regenerate both refuse
    assert client.put("/api/grading/drafts/王明_报告", json={"grade": 1}).status_code == 409
    assert (
        client.post("/api/grading/drafts/王明_报告/regenerate", json={"guidance": "x"}).status_code
        == 409
    )

    # reopen unlocks
    r = client.post("/api/grading/drafts/王明_报告/reopen")
    assert r.json()["status"] == "draft"
    assert client.put("/api/grading/drafts/王明_报告", json={"grade": 97}).status_code == 200


def test_regenerate_with_guidance(client):
    r = client.post("/api/grading/drafts/王明_报告/regenerate", json={"guidance": "评语更简短"})
    assert r.status_code == 200
    body = r.json()
    assert body["grade"] == 92  # from the fake redraft
    assert body["last_guidance"] == "评语更简短"
    assert body["status"] == "draft"


def test_export_csv_only_finalized(client):
    csv_before = client.get("/api/grading/export.csv").text
    assert "王明" not in csv_before  # still a draft -> not exported

    client.post("/api/grading/drafts/王明_报告/finalize")
    csv_after = client.get("/api/grading/export.csv").text
    assert "王明" in csv_after and "95" in csv_after


def test_grading_page_serves(client):
    r = client.get("/cohort/grading")
    assert r.status_code == 200
    assert "grading.js" in r.text
