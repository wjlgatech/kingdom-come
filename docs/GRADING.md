# AI-Assisted Report Grading (M1: grading engine)

Drafts grades and pastoral comments for 《属灵操练练习》 reports in 陈老师's own
voice, learned from his past comment corpus. **Every output is a draft** — the
professor reviews, edits, and finalizes each one before anything reaches a
student. The AI never grades autonomously.

## Privacy posture: cloud with consent

Student reports are confessional documents. The rules:

1. **Consent is collected up front.** Add this line to the assignment
   instructions (adapt as 陈老师 sees fit):

   > 本课程的期末报告将在陈老师的监督下使用 AI 辅助批改：报告内容会通过加密
   > 渠道发送给云端 AI 服务，仅用于生成初步评语草稿；该服务不会将你的报告用于
   > AI 模型训练；最终分数与评语均由陈老师亲自审定。如你不希望报告经 AI 辅助
   > 处理，请在提交时注明，陈老师将全程手工批改，不影响成绩。

2. **Opt-outs are honored** — exclude those files from the batch folder.
3. **The comment corpus never enters the repo.** `backend/grading/data/corpus/`
   is gitignored; only the distilled `voice_profile.json` is committed.
4. **API-tier requests are not used for provider model training** (Anthropic
   and OpenAI API terms). Keys live in env vars, never in code.

## Setup

```bash
pip install -e ".[grading]"          # adds anthropic + pypdf
export ANTHROPIC_API_KEY=sk-ant-...  # preferred (claude-opus-5); or OPENAI_API_KEY
```

Ingest the voice corpus once (from the professor's comments document):

```bash
textutil -convert txt 大作业评语2023年8月底.docx -stdout > /tmp/comments.txt
python -m backend.grading.corpus /tmp/comments.txt \
    --out backend/grading/data/corpus/zuxing_2023.json
```

## Usage

```bash
# Draft grades for a folder of submissions (PDF or txt)
python -m backend.grading.batch --reports ./submissions --out ./drafts

# Judge draft comments against the real corpus (voice-fidelity gate)
python -m backend.grading.evaluate --drafts ./drafts --threshold 0.75
```

Each draft JSON carries: `grade`, `comment` (student-facing after review),
`rationale` (professor-only), `flags`/`flag_notes` (structural issues —
missing sections, too short; **flags route to human attention, never to
automatic penalties**), and `needs_attention`.

## Eval harness — honest limitation

The 2023 corpus contains comments only (not the reports they answered), so
`evaluate.py` measures **style fidelity** against exemplars: structure,
quoting-the-report, register, warmth, theology, each 1–5 by an LLM judge.
The operational metric that supersedes it once live: **% of drafts the
professor finalizes with only minor edits** (tracked in the M2 review surface).

## Roadmap

- **M2** — review surface in the kingdom-come web UI: report + draft
  side-by-side, edit, finalize; export comment docs + gradebook CSV.
- **M3** — cohort synthesis: demand/supply analysis of formation needs,
  advice for future teaching/counseling, signals into the formation platform.
- **M4** — intake portal (upload, filename/format validation, receipts,
  deadline tracking) + local-model option.
