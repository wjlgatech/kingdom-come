"""Unit tests for the grading module — no network, LLM faked via GRADING_FAKE_RESPONSE."""

import json

import pytest

from backend.grading.checks import count_cjk, structure_flags
from backend.grading.corpus import parse_comments_text
from backend.grading.extract import parse_student_name
from backend.grading.grader import build_system_prompt, draft_grade, load_voice_profile

SAMPLE_COMMENTS = """陈老师对大作业评语
前言若干，不属于任何一条评语。

XXX同学
谢谢你所写的属灵操练报告。为你的收获感恩。
祝福你跟主的关系与日俱增。
陈老师

.XXX同学
含着眼泪读完你的报告。
以马内利
陈老师
"""

GOOD_REPORT = (
    "我在操练提议中选择了默想、禁食与独处三种属灵操练方式。"
    + "在这六周的操练经历中，我学到了许多，有顺利也有挣扎。" * 200
    + "最后，我的退省经历：我独自去了海边的退修中心，在那里安静了两天。"
)

FAKE_RESPONSE = json.dumps(
    {
        "grade": 95,
        "comment": "王明同学\n谢谢你所写的属灵操练报告。\n为你的收获感恩。\n陈老师",
        "rationale": "三部分齐全，退省描述具体。",
    },
    ensure_ascii=False,
)


class TestCorpus:
    def test_parses_exemplars(self):
        exemplars = parse_comments_text(SAMPLE_COMMENTS)
        assert len(exemplars) == 2
        assert all(e.startswith("XXX同学") for e in exemplars)
        assert all(e.endswith("陈老师") for e in exemplars)

    def test_drops_preamble(self):
        exemplars = parse_comments_text(SAMPLE_COMMENTS)
        assert "前言若干" not in "".join(exemplars)


class TestChecks:
    def test_good_report_has_no_flags(self):
        assert structure_flags(GOOD_REPORT) == []

    def test_short_report_missing_retreat(self):
        flags = structure_flags("我选择了操练提议中的默想。这六周的经历让我学到很多。")
        assert "missing_section_retreat" in flags
        assert "too_short" in flags

    def test_empty_report(self):
        assert structure_flags("   ") == ["empty_report"]

    def test_count_cjk_ignores_ascii(self):
        assert count_cjk("abc 属灵操练 123") == 4


class TestExtract:
    def test_student_name_from_convention(self):
        assert parse_student_name("Zhang baoluo（姓名）_《属灵操练的练习》报告.pdf") == "Zhang baoluo（姓名）"

    def test_student_name_fallback_to_stem(self):
        assert parse_student_name("report.pdf") == "report"


class TestGrader:
    def test_draft_grade_parses_fake_response(self, monkeypatch):
        monkeypatch.setenv("GRADING_FAKE_RESPONSE", FAKE_RESPONSE)
        draft = draft_grade("王明", GOOD_REPORT)
        assert draft.grade == 95
        assert draft.student == "王明"
        assert "陈老师" in draft.comment
        assert draft.needs_attention is False

    def test_below_baseline_needs_attention(self, monkeypatch):
        low = json.loads(FAKE_RESPONSE)
        low["grade"] = 85
        monkeypatch.setenv("GRADING_FAKE_RESPONSE", json.dumps(low, ensure_ascii=False))
        draft = draft_grade("王明", GOOD_REPORT)
        assert draft.needs_attention is True

    def test_structural_flags_force_attention(self, monkeypatch):
        monkeypatch.setenv("GRADING_FAKE_RESPONSE", FAKE_RESPONSE)
        draft = draft_grade("王明", "很短的报告，只提到操练提议和六周经历学到的。")
        assert draft.flags
        assert draft.needs_attention is True
        assert draft.grade == 95  # flags never lower the drafted grade

    def test_json_wrapped_in_prose_still_parses(self, monkeypatch):
        monkeypatch.setenv("GRADING_FAKE_RESPONSE", f"好的，以下是草稿：\n{FAKE_RESPONSE}\n希望有帮助。")
        draft = draft_grade("王明", GOOD_REPORT)
        assert draft.grade == 95

    def test_system_prompt_includes_exemplars_and_structure(self):
        profile = load_voice_profile()
        prompt = build_system_prompt(profile, ["XXX同学\n谢谢你。\n陈老师"])
        assert "评语范例" in prompt
        assert "陈老师" in prompt
        assert "JSON" in prompt


class TestBatch:
    def test_batch_over_txt_reports(self, tmp_path, monkeypatch):
        from backend.grading.batch import run_batch

        monkeypatch.setenv("GRADING_FAKE_RESPONSE", FAKE_RESPONSE)
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / "王明_《属灵操练的练习》报告.txt").write_text(GOOD_REPORT, encoding="utf-8")
        (reports / "李四_《属灵操练的练习》报告.txt").write_text("太短了", encoding="utf-8")
        out = tmp_path / "drafts"

        summary = run_batch(reports, out, corpus_path=None)

        assert summary["total"] == 2
        assert summary["drafted"] == 2
        assert summary["needs_attention"] == ["李四"]
        draft = json.loads((out / "王明_《属灵操练的练习》报告.json").read_text(encoding="utf-8"))
        assert draft["grade"] == 95
        assert (out / "summary.json").exists()

    def test_batch_records_errors_and_continues(self, tmp_path, monkeypatch):
        from backend.grading.batch import run_batch

        def boom(system, user):
            raise RuntimeError("api down")

        # No fake response -> draft_grade uses real llm; patch it instead
        monkeypatch.delenv("GRADING_FAKE_RESPONSE", raising=False)
        import backend.grading.grader as grader_mod

        monkeypatch.setattr(grader_mod, "complete", boom)
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / "王明_报告.txt").write_text(GOOD_REPORT, encoding="utf-8")
        out = tmp_path / "drafts"

        summary = run_batch(reports, out)
        assert summary["drafted"] == 0
        assert "王明_报告.txt" in summary["errors"]


class TestJudge:
    def test_judge_parses_scores(self, monkeypatch):
        from backend.grading.evaluate import judge_voice_fidelity

        fake = json.dumps(
            {"scores": {"structure": 5, "quoting": 4, "register": 5, "warmth": 5, "theology": 4}, "verdict": "接近真迹"},
            ensure_ascii=False,
        )
        monkeypatch.setenv("GRADING_FAKE_RESPONSE", fake)
        result = judge_voice_fidelity("草稿", ["范例"])
        assert result["mean"] == pytest.approx(23 / 25)
        assert result["verdict"] == "接近真迹"
