"""M3: cohort synthesis — from finalized reports to formation intelligence.

Pipeline (finalized drafts only — unreviewed data never feeds analytics):

  1. extract_signals(): one LLM call per report -> structured formation
     signals (disciplines practiced, struggles, breakthroughs, needs, retreat
     shape, readiness to lead others). Cached on the draft JSON, so re-runs
     only pay for new finalizations.
  2. aggregate(): deterministic Python — discipline supply counts, need
     demand counts, struggle themes. No LLM, so the numbers are auditable.
  3. write_advisory(): one LLM call turns the aggregate into 陈老师-facing
     prose — demand/supply reading, advice for next semester's teaching, and
     counseling attention points.

Output: grading_data/synthesis.json (aggregate + advisory + provenance).
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Callable

from . import store
from .llm import complete

SIGNAL_KEYS = ["disciplines", "struggles", "breakthroughs", "needs", "retreat", "leading_readiness"]

EXTRACT_SYSTEM = (
    "你是神学院《灵命塑造》课程的数据整理助手。从一份学生的属灵操练报告及教授评语中"
    "提取结构化信号。只输出 JSON，所有数组元素用简短中文短语（2-8字）：\n"
    '{"disciplines": ["学生实际操练的属灵操练方式"],\n'
    ' "struggles": ["学生遇到的主要挣扎/困难"],\n'
    ' "breakthroughs": ["学生的主要突破/收获"],\n'
    ' "needs": ["该学生后续需要的教导或关怀，如：时间管理指导、哀伤辅导"],\n'
    ' "retreat": "退省形式一句话（如：独自山上两天）",\n'
    ' "leading_readiness": "对将来带领他人操练的准备程度一句话"}'
)

ADVISORY_SYSTEM = (
    "你是陈老师的教学顾问。根据全班属灵操练报告的汇总信号，为陈老师写一份《班级属灵光景与教学建议》。"
    "务实、具体、牧养导向。结构：\n"
    "## 供给面：学生们在操练什么\n## 需求面：学生们需要什么\n"
    "## 下学期教学建议\n## 需要关怀跟进的方向\n"
    "只依据给你的汇总数据，不要杜撰。用中文，600-900字。"
)


def _parse_json_object(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON object in model response: {text[:200]!r}")
    return json.loads(match.group(0), strict=False)  # local models emit raw newlines in strings


def extract_signals(report_text: str, comment: str, llm: Callable[[str, str], str] | None = None) -> dict:
    llm = llm or complete
    user = f"## 学生报告\n{report_text}\n\n## 教授定稿评语\n{comment}"
    data = _parse_json_object(llm(EXTRACT_SYSTEM, user))
    return {k: data.get(k) or ([] if k not in ("retreat", "leading_readiness") else "") for k in SIGNAL_KEYS}


def aggregate(all_signals: list[dict]) -> dict:
    """Deterministic counts — the auditable half of the synthesis."""
    supply = Counter()
    demand = Counter()
    struggles = Counter()
    for s in all_signals:
        supply.update(s.get("disciplines") or [])
        demand.update(s.get("needs") or [])
        struggles.update(s.get("struggles") or [])
    return {
        "students": len(all_signals),
        "discipline_supply": dict(supply.most_common()),
        "need_demand": dict(demand.most_common()),
        "struggle_themes": dict(struggles.most_common()),
    }


def write_advisory(agg: dict, llm: Callable[[str, str], str] | None = None) -> str:
    llm = llm or complete
    return llm(ADVISORY_SYSTEM, json.dumps(agg, ensure_ascii=False, indent=2)).strip()


def run_synthesis(llm: Callable[[str, str], str] | None = None) -> dict:
    """Extract (with per-draft caching) -> aggregate -> advisory -> persist."""
    finalized = [d for d in store.list_drafts() if d["status"] == "final"]
    if not finalized:
        raise ValueError("no finalized drafts yet — synthesis reads only professor-approved data")

    all_signals: list[dict] = []
    for item in finalized:
        draft = store.get_draft(item["id"])
        signals = draft.get("signals")
        if not signals:
            report_text = store.report_text_for(item["id"])
            if not report_text:
                continue  # no source document — skip, never guess
            signals = extract_signals(report_text, draft.get("comment", ""), llm=llm)
            draft["signals"] = signals
            store.save_draft(item["id"], draft)
        all_signals.append(signals)

    if not all_signals:
        raise ValueError("no finalized drafts with readable report files")

    agg = aggregate(all_signals)
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "aggregate": agg,
        "advisory": write_advisory(agg, llm=llm),
    }
    path = store.root_dir() / "synthesis.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def latest_synthesis() -> dict | None:
    path = store.root_dir() / "synthesis.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
