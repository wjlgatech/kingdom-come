"""Voice corpus: the professor's past comments, used as few-shot exemplars.

The raw corpus stays LOCAL and gitignored (backend/grading/data/corpus/) —
these are the professor's own writings and must not land in the public repo.
Only the distilled voice_profile.json is committed.

Ingest once from the plain-text export of the comments document:

    textutil -convert txt 大作业评语.docx -stdout > /tmp/comments.txt
    python -m backend.grading.corpus /tmp/comments.txt \
        --out backend/grading/data/corpus/zuxing_2023.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SIGNATURE = "陈老师"
GREETING_RE = re.compile(r"^\.?\s*(XXX|[一-鿿]{2,4})同学\s*$")

DEFAULT_CORPUS_DIR = Path(__file__).parent / "data" / "corpus"


def parse_comments_text(text: str) -> list[str]:
    """Split a plain-text comments document into individual comment exemplars.

    A comment starts at a greeting line ("XXX同学") and ends at the signature
    line ("陈老师"). Preamble before the first greeting is dropped.
    """
    exemplars: list[str] = []
    current: list[str] | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if GREETING_RE.match(line):
            if current:  # unterminated previous comment: keep what we have
                exemplars.append("\n".join(current).strip())
            current = [line.lstrip(". ")]
            continue
        if current is None:
            continue
        current.append(line)
        if line == SIGNATURE:
            exemplars.append("\n".join(current).strip())
            current = None
    if current:
        exemplars.append("\n".join(current).strip())
    return [e for e in exemplars if e]


def load_corpus(path: str | Path | None = None) -> list[str]:
    """Load exemplars from a corpus JSON file, or from the default corpus dir.

    Returns [] when no corpus is present — the grader still works, on the
    voice profile alone, but voice fidelity will be weaker.
    """
    if path is not None:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return list(data.get("exemplars", []))
    exemplars: list[str] = []
    if DEFAULT_CORPUS_DIR.is_dir():
        for f in sorted(DEFAULT_CORPUS_DIR.glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            exemplars.extend(data.get("exemplars", []))
    return exemplars


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Ingest a comments text file into a corpus JSON.")
    parser.add_argument("source", help="plain-text export of the comments document")
    parser.add_argument("--out", required=True, help="output corpus JSON path (keep it gitignored)")
    args = parser.parse_args()

    text = Path(args.source).read_text(encoding="utf-8")
    exemplars = parse_comments_text(text)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps({"exemplars": exemplars}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"wrote {len(exemplars)} exemplars -> {out}")


if __name__ == "__main__":
    main()
