"""Batch CLI: a folder of report submissions -> per-student draft JSON + summary.

    python -m backend.grading.batch --reports ./submissions --out ./drafts

Every draft is exactly that — a draft. The professor reviews, edits, and
finalizes each one before anything reaches a student (M2 review surface).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .corpus import load_corpus
from .extract import SUPPORTED_SUFFIXES, extract_text, parse_student_name
from .grader import draft_grade, load_voice_profile


def run_batch(reports_dir: Path, out_dir: Path, corpus_path: Path | None = None) -> dict:
    profile = load_voice_profile()
    exemplars = load_corpus(corpus_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(p for p in reports_dir.iterdir() if p.suffix.lower() in SUPPORTED_SUFFIXES)
    summary: dict = {
        "total": len(files),
        "drafted": 0,
        "needs_attention": [],
        "optouts": [],
        "errors": {},
        "exemplars_used": len(exemplars),
    }
    for path in files:
        student = parse_student_name(path)
        if (reports_dir / f"{path.stem}.optout").exists():
            # Student declined AI-assisted grading (docs/GRADING.md): honor it.
            summary["optouts"].append(student)
            print(f"  ○ {student}: 学生选择手工批改，已跳过")
            continue
        try:
            text = extract_text(path)
            draft = draft_grade(student, text, profile=profile, exemplars=exemplars)
        except Exception as exc:
            summary["errors"][path.name] = str(exc)
            print(f"  ✗ {student}: {exc}")
            continue
        out_file = out_dir / f"{path.stem}.json"
        out_file.write_text(draft.model_dump_json(indent=2), encoding="utf-8")
        summary["drafted"] += 1
        if draft.needs_attention:
            summary["needs_attention"].append(student)
        marker = "⚠" if draft.needs_attention else "✓"
        print(f"  {marker} {student}: {draft.grade}" + (f"  [{'; '.join(draft.flag_notes)}]" if draft.flags else ""))

    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Draft grades for a folder of report submissions.")
    parser.add_argument("--reports", required=True, help="folder of student submissions (PDF/txt)")
    parser.add_argument("--out", required=True, help="output folder for draft JSONs")
    parser.add_argument("--corpus", default=None, help="corpus JSON (default: backend/grading/data/corpus/)")
    args = parser.parse_args()

    summary = run_batch(
        Path(args.reports), Path(args.out), Path(args.corpus) if args.corpus else None
    )
    print(
        f"\n{summary['drafted']}/{summary['total']} drafted, "
        f"{len(summary['needs_attention'])} flagged for attention, "
        f"{len(summary['errors'])} errors"
    )


if __name__ == "__main__":
    main()
