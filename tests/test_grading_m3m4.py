"""M3 synthesis + M4 intake tests — no network, LLM faked."""

import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.grading.synthesis import aggregate, extract_signals

REPORT = "我在操练提议中选择了默想与禁食。" + "六周经历。" * 400 + "退省经历：山上营地。"

SIGNALS_RESPONSE = json.dumps(
    {
        "disciplines": ["默想", "禁食"],
        "struggles": ["起早困难"],
        "breakthroughs": ["经历安息"],
        "needs": ["时间管理指导"],
        "retreat": "独自山上两天",
        "leading_readiness": "有初步构想",
    },
    ensure_ascii=False,
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("KC_GRADING_DIR", str(tmp_path))
    (tmp_path / "reports").mkdir()
    (tmp_path / "drafts").mkdir()
    return TestClient(app)


def _seed_draft(tmp_path, name="王明_报告", status="final", signals=None):
    draft = {
        "student": name.split("_")[0], "grade": 95, "comment": "评语", "rationale": "",
        "flags": [], "flag_notes": [], "needs_attention": False, "status": status,
    }
    if signals:
        draft["signals"] = signals
    (tmp_path / "drafts" / f"{name}.json").write_text(
        json.dumps(draft, ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "reports" / f"{name}.txt").write_text(REPORT, encoding="utf-8")


class TestSynthesisUnit:
    def test_extract_signals_parses(self, monkeypatch):
        monkeypatch.setenv("GRADING_FAKE_RESPONSE", SIGNALS_RESPONSE)
        s = extract_signals(REPORT, "评语")
        assert s["disciplines"] == ["默想", "禁食"]
        assert s["retreat"] == "独自山上两天"

    def test_aggregate_is_deterministic(self):
        signals = [
            {"disciplines": ["默想", "禁食"], "needs": ["时间管理指导"], "struggles": ["起早困难"]},
            {"disciplines": ["默想"], "needs": ["哀伤辅导"], "struggles": ["起早困难"]},
        ]
        agg = aggregate(signals)
        assert agg["students"] == 2
        assert agg["discipline_supply"]["默想"] == 2
        assert agg["struggle_themes"]["起早困难"] == 2
        assert set(agg["need_demand"]) == {"时间管理指导", "哀伤辅导"}


class TestSynthesisAPI:
    def test_synthesis_requires_finalized_drafts(self, client, tmp_path):
        _seed_draft(tmp_path, status="draft")
        assert client.post("/api/grading/synthesis").status_code == 409

    def test_synthesis_runs_and_persists(self, client, tmp_path, monkeypatch):
        # signals already cached on the draft -> only the advisory hits the LLM
        _seed_draft(tmp_path, signals=json.loads(SIGNALS_RESPONSE))
        monkeypatch.setenv("GRADING_FAKE_RESPONSE", "## 供给面\n默想为主。")
        r = client.post("/api/grading/synthesis")
        assert r.status_code == 200
        body = r.json()
        assert body["aggregate"]["students"] == 1
        assert "供给面" in body["advisory"]
        # persisted and retrievable
        assert client.get("/api/grading/synthesis").json()["aggregate"]["students"] == 1

    def test_get_before_any_run_is_404(self, client):
        assert client.get("/api/grading/synthesis").status_code == 404


class TestIntake:
    def _upload(self, client, filename, content=b"%PDF-1.4 fake", consent="yes"):
        return client.post(
            "/api/grading/submissions",
            files={"file": (filename, content, "application/pdf")},
            data={"consent": consent},
        )

    def test_valid_upload_gets_receipt(self, client):
        r = self._upload(client, "王明_《属灵操练的练习》报告.pdf")
        assert r.status_code == 200
        body = r.json()
        assert body["student"] == "王明"
        assert body["ai_consent"] is True
        assert body["warnings"] == [] or all("截止" in w for w in body["warnings"])

    def test_non_pdf_rejected_in_chinese(self, client):
        r = self._upload(client, "报告.docx")
        assert r.status_code == 422
        assert "PDF" in r.json()["detail"]

    def test_bad_filename_warns_but_accepts(self, client):
        r = self._upload(client, "wangming-report.pdf")
        assert r.status_code == 200
        assert any("文件名不符合" in w for w in r.json()["warnings"])

    def test_optout_accepted_and_marked(self, client, tmp_path):
        r = self._upload(client, "李四_《属灵操练的练习》报告.pdf", consent="no")
        assert r.status_code == 200
        assert any("手工批改" in w for w in r.json()["warnings"])
        assert (tmp_path / "reports" / "李四_《属灵操练的练习》报告.optout").exists()
        subs = client.get("/api/grading/submissions").json()["submissions"]
        assert subs[0]["ai_consent"] is False

    def test_optout_skipped_by_batch(self, client, tmp_path, monkeypatch):
        from backend.grading.batch import run_batch

        self._upload(client, "李四_《属灵操练的练习》报告.pdf", consent="no")
        monkeypatch.setenv(
            "GRADING_FAKE_RESPONSE",
            json.dumps({"grade": 95, "comment": "c\n陈老师", "rationale": ""}, ensure_ascii=False),
        )
        summary = run_batch(tmp_path / "reports", tmp_path / "drafts")
        assert summary["optouts"] == ["李四"]
        assert summary["drafted"] == 0

    def test_late_detection(self, client, monkeypatch):
        monkeypatch.setenv("KC_GRADING_DEADLINE", "2020-01-01T00:00:00+00:00")
        r = self._upload(client, "王明_《属灵操练的练习》报告.pdf")
        assert r.json()["late"] is True
        assert any("截止时间" in w for w in r.json()["warnings"])

    def test_path_traversal_stripped(self, client, tmp_path):
        r = self._upload(client, "../../evil_《属灵操练的练习》报告.pdf")
        assert r.status_code == 200
        # saved inside reports/, not above it
        saved = list((tmp_path / "reports").glob("*.pdf"))
        assert len(saved) == 1 and ".." not in saved[0].name

    def test_resubmission_replaces_with_notice(self, client):
        self._upload(client, "王明_《属灵操练的练习》报告.pdf")
        r = self._upload(client, "王明_《属灵操练的练习》报告.pdf")
        assert r.json()["resubmitted"] is True
        assert any("覆盖" in w for w in r.json()["warnings"])

    def test_submit_page_serves(self, client):
        r = client.get("/submit")
        assert r.status_code == 200
        assert "submit.js" in r.text
