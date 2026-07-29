"""Deterministic structural checks on a report.

Checks produce FLAGS for the professor's attention — never grade penalties.
A flagged report is routed to human judgment, not auto-marked-down.
"""

from __future__ import annotations

import re

CJK_RE = re.compile(r"[一-鿿]")

EXPECTED_CHARS = 8000  # ~10 pages per the assignment
MIN_CHARS = 4000  # below half the expected length -> flag

SECTION_KEYWORDS = {
    "missing_section_disciplines": ["操练提议", "操练方式", "属灵操练"],
    "missing_section_experience": ["六周", "经历", "学到"],
    "missing_section_retreat": ["退省", "退修"],
}

FLAG_LABELS = {
    "missing_section_disciplines": "未找到第一部分：所选属灵操练方式的介绍",
    "missing_section_experience": "未找到第二部分：六周操练经历与所学",
    "missing_section_retreat": "未找到第三部分：退省经历",
    "too_short": f"篇幅明显不足（少于 {MIN_CHARS} 字，要求约 {EXPECTED_CHARS} 字）",
    "empty_report": "报告内容为空或无法提取文本",
}


def count_cjk(text: str) -> int:
    return len(CJK_RE.findall(text))


def structure_flags(text: str) -> list[str]:
    """Return flag codes for structural issues. Empty list = no issues found."""
    if not text.strip():
        return ["empty_report"]
    flags: list[str] = []
    for flag, keywords in SECTION_KEYWORDS.items():
        if not any(kw in text for kw in keywords):
            flags.append(flag)
    if count_cjk(text) < MIN_CHARS:
        flags.append("too_short")
    return flags


def describe_flags(flags: list[str]) -> list[str]:
    return [FLAG_LABELS.get(f, f) for f in flags]
