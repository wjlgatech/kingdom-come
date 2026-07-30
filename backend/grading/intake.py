"""M4: submission intake — validation, receipts, deadline tracking.

Students upload PDFs at /submit. Rules encode the assignment sheet:
PDF only, the filename convention "姓名_《属灵操练的练习》报告.pdf", and the
deadline (KC_GRADING_DEADLINE, ISO-8601; default 2026-08-17 23:59 US Eastern
per the syllabus). A wrong filename is a WARNING on the receipt, not a
rejection — students shouldn't be locked out by punctuation. Consent is
required (the cloud-with-consent posture in docs/GRADING.md); an opt-out
upload is accepted and marked so the professor grades it by hand.
"""

from __future__ import annotations

import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from . import store
from .extract import parse_student_name

DEFAULT_DEADLINE = "2026-08-17T23:59:00-04:00"
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # a 10-page PDF is well under this
NAME_CONVENTION_RE = re.compile(r"^[^_]+_《属灵操练的练习》报告\.pdf$")


def deadline() -> datetime:
    return datetime.fromisoformat(os.getenv("KC_GRADING_DEADLINE", DEFAULT_DEADLINE))


def sanitize_filename(filename: str) -> str:
    """Keep the CJK-friendly basename; strip path separators and control chars."""
    name = Path(filename).name  # drops any directory components
    name = unicodedata.normalize("NFC", name)
    name = "".join(ch for ch in name if ch.isprintable() and ch not in '/\\:*?"<>|')
    if not name or name.startswith("."):
        raise ValueError("文件名无效")
    return name


def validate_upload(filename: str, size: int) -> list[str]:
    """Hard failures only — raise ValueError with a student-readable message."""
    problems = []
    if not filename.lower().endswith(".pdf"):
        raise ValueError("请提交 PDF 格式的报告（作业要求第 3 条）")
    if size == 0:
        raise ValueError("上传的文件是空的，请检查后重新上传")
    if size > MAX_UPLOAD_BYTES:
        raise ValueError("文件超过 25MB，请压缩后重新上传")
    return problems


def receipt_for(filename: str, size: int, consent: bool, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    warnings = []
    if not NAME_CONVENTION_RE.match(filename):
        warnings.append(
            "文件名不符合要求的格式「姓名_《属灵操练的练习》报告.pdf」——已收到你的报告，但请留意下次命名。"
        )
    late = now > deadline()
    if late:
        warnings.append("此份报告在截止时间（2026年08月17日 23:59）之后提交，将由陈老师酌情处理。")
    if not consent:
        warnings.append("你选择了不使用 AI 辅助批改，陈老师将全程手工批改你的报告。")
    return {
        "student": parse_student_name(filename),
        "filename": filename,
        "size": size,
        "received_at": now.isoformat(),
        "deadline": deadline().isoformat(),
        "late": late,
        "ai_consent": consent,
        "warnings": warnings,
    }


def save_submission(filename: str, content: bytes, consent: bool) -> dict:
    filename = sanitize_filename(filename)
    validate_upload(filename, len(content))
    reports = store.reports_dir()
    reports.mkdir(parents=True, exist_ok=True)
    dest = reports / filename
    if dest.exists():  # resubmission: replace, note it on the receipt
        resubmitted = True
    else:
        resubmitted = False
    dest.write_bytes(content)

    receipt = receipt_for(filename, len(content), consent)
    if resubmitted:
        receipt["warnings"].append("这份报告覆盖了你之前的提交——以本次为准。")
    # Opt-outs are marked next to the file so the batch run skips them.
    if not consent:
        (reports / f"{dest.stem}.optout").write_text("manual grading requested", encoding="utf-8")
    receipt["resubmitted"] = resubmitted
    return receipt


def list_submissions() -> list[dict]:
    reports = store.reports_dir()
    items = []
    if reports.is_dir():
        for f in sorted(reports.glob("*.pdf")):
            stat = f.stat()
            items.append(
                {
                    "student": parse_student_name(f),
                    "filename": f.name,
                    "size": stat.st_size,
                    "received_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    "ai_consent": not (reports / f"{f.stem}.optout").exists(),
                }
            )
    return items
