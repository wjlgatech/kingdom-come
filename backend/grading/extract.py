"""Report intake: extract text from a submission file, parse the student name.

Filename convention from the assignment: "Zhang baoluo（姓名）_《属灵操练的练习》报告.pdf"
-> the student name is everything before the first underscore.
"""

from __future__ import annotations

from pathlib import Path

SUPPORTED_SUFFIXES = {".pdf", ".txt", ".md"}


def parse_student_name(filename: str | Path) -> str:
    stem = Path(filename).stem
    return stem.split("_", 1)[0].strip() or stem


def extract_text(path: str | Path) -> str:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".txt", ".md"):
        return path.read_text(encoding="utf-8")
    if suffix == ".pdf":
        return _extract_pdf(path)
    raise ValueError(f"unsupported submission format: {path.name} (expected PDF)")


def _extract_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "pypdf is required for PDF extraction — install with: pip install -e '.[grading]'"
        ) from exc
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)
