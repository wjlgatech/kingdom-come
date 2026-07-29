"""Voice-fidelity eval harness: LLM-judge scores drafted comments against
the professor's real comment corpus.

Honest limitation: the 2023 corpus contains comments only, not the reports
they responded to, so this judges STYLE fidelity (structure, register,
warmth, theology, evidence-of-close-reading) against exemplars — not
report→comment correctness. The operational metric that supersedes this is
the % of drafts the professor finalizes with only minor edits (M2).

    python -m backend.grading.evaluate --drafts ./drafts --threshold 0.75
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Callable

from .corpus import load_corpus
from .llm import complete

DIMENSIONS = {
    "structure": "是否遵循结构：称呼学生→感谢→回应/引用报告内容→具体肯定→劝勉→祝福→陈老师落款",
    "quoting": "是否引用或具体回应了报告原文（证明认真读过），而非泛泛套话",
    "register": "语气是否符合范例：温暖、牧养、短句分行、常用语（以马内利、为你加油等）自然出现",
    "warmth": "鼓励与肯定是否真诚具体，符合 encouragement-first 的批改哲学",
    "theology": "神学表达是否健康且符合范例的核心主题（创造主/救赎主与人的爱的关系）",
}

JUDGE_SYSTEM = (
    "你是文风评审。给你若干陈老师亲笔评语范例和一条 AI 起草的评语，"
    "判断草稿是否像陈老师本人所写。对每个维度打 1-5 分（5=难以与真迹区分）。"
    '只输出 JSON：{"scores": {"structure": n, "quoting": n, "register": n, "warmth": n, "theology": n}, "verdict": "<一句话总评>"}'
)


def judge_voice_fidelity(
    candidate: str,
    exemplars: list[str],
    llm: Callable[[str, str], str] = complete,
) -> dict:
    user = (
        "## 维度定义\n"
        + "\n".join(f"- {k}: {v}" for k, v in DIMENSIONS.items())
        + "\n\n## 陈老师真迹范例\n\n"
        + "\n\n---\n\n".join(exemplars[:8])
        + "\n\n## 待评审的 AI 草稿\n\n"
        + candidate
    )
    raw = llm(JUDGE_SYSTEM, user)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON in judge response: {raw[:200]!r}")
    data = json.loads(match.group(0))
    scores = {k: int(v) for k, v in data["scores"].items()}
    data["mean"] = round(sum(scores.values()) / (len(scores) * 5), 3)  # normalized 0-1
    data["scores"] = scores
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Judge drafted comments against the voice corpus.")
    parser.add_argument("--drafts", required=True, help="folder of draft JSONs from batch.py")
    parser.add_argument("--corpus", default=None, help="corpus JSON (default: local corpus dir)")
    parser.add_argument("--threshold", type=float, default=0.75, help="mean fidelity gate (0-1)")
    args = parser.parse_args()

    exemplars = load_corpus(Path(args.corpus) if args.corpus else None)
    if not exemplars:
        raise SystemExit("no corpus exemplars found — ingest one first (see corpus.py docstring)")

    results = []
    for f in sorted(Path(args.drafts).glob("*.json")):
        if f.name == "summary.json":
            continue
        draft = json.loads(f.read_text(encoding="utf-8"))
        verdict = judge_voice_fidelity(draft["comment"], exemplars)
        results.append({"student": draft["student"], **verdict})
        print(f"  {draft['student']}: {verdict['mean']:.2f}  {verdict['verdict']}")

    if not results:
        raise SystemExit("no drafts found")
    overall = round(sum(r["mean"] for r in results) / len(results), 3)
    gate = "PASS" if overall >= args.threshold else "FAIL"
    print(f"\nvoice fidelity: {overall:.3f} (threshold {args.threshold}) -> {gate}")
    raise SystemExit(0 if gate == "PASS" else 1)


if __name__ == "__main__":
    main()
