# V7 Features

## Predictive

`POST /predictive/dropout-risk`

Scores student dropout risk from engagement and reflection signals. The response includes:

- `score`
- `level`
- `reasons`

## Adaptive

`POST /curriculum/recommendations`

Recommends curriculum from calling and previously completed content.

## Outcomes

`POST /outcomes`

Records a ministry outcome snapshot and returns an effectiveness band. SQLAlchemy model support lives in `backend.models.outcome.MinistryOutcome`.

## Orchestration

`POST /orchestration/actions`

Returns actionable class adjustments with group identifiers, reasons, and member counts.

## Web Workbench

`GET /`

Serves the public workbench UI from `frontend/`. The UI exercises the same JSON endpoints external integrations use.

## Cohort & student API

Agent-facing JSON reads, namespaced under `/api/` so they don't collide with the Jinja page route at `/students/{id}`:

- `GET /api/students` — full cohort roster; `?cohort_id=...` filters.
- `GET /api/students/{id}` — single student profile (reflections, outcomes, risk history).
- `GET /api/cohorts/{id}` — cohort metadata (name, director, student count).
- `GET /api/cohorts/{id}/outcomes` — outcomes feed for the cohort, newest first.

Backed by `backend/fixtures/cohort.py` (ported from `frontend/cohort_data.js`).

## MCP server

`mcp_server/server.py` exposes nine MCP tools over stdio so any MCP-aware agent harness (Claude Code, Codex, OpenCode, …) can use Kingdom Come as a tool surface:

- `dropout_risk`, `curriculum_recommend`, `orchestration_plan`, `log_outcome`
- `list_students`, `get_student`, `get_cohort`, `list_cohort_outcomes`
- `chat_with_mentor` (drains the WS pipeline; returns memory + full reply)

Install with `pip install -e ".[mcp]"` and run `python -m mcp_server.server`. Wiring snippets for each harness live in [`AGENTS.md`](AGENTS.md); the Claude Code plugin manifest is at `.claude-plugin/plugin.json`.

## Verification

Run `python -m pytest` before shipping changes.
