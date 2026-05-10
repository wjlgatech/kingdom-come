# Architecture

Kingdom Come is intentionally small and contributor-friendly.

## Runtime

- `backend/app.py` owns the FastAPI app, request schemas, routes, and static UI serving.
- `backend/services/` contains pure domain functions that are easy to test.
- `backend/models/` contains SQLAlchemy models.
- `backend/fixtures/cohort.py` is the in-memory cohort/student source for the `/api/...` read endpoints. Ported from `frontend/cohort_data.js`; replace with a real persistence layer when the product crosses that line.
- `backend/db/connection.py` defines the SQLAlchemy base, engine, session factory, and metadata initialization helper.
- `frontend/` contains static HTML, CSS, and JavaScript served by FastAPI.
- `mcp_server/server.py` wraps the FastAPI as MCP tools so agent harnesses (Claude Code, Codex, OpenCode, …) can call into a running KC instance over stdio.
- `backend/services/prayer.py` runs the prayer + prophecy ledgers (in-process state, dataclass entities). Two ledgers, one weighing rule (1 Cor 14:29: 2-of-3), one visibility model. See [`PRAYER.md`](PRAYER.md) for the full data model.

## Agent integration

The MCP server is documented in [`docs/AGENTS.md`](AGENTS.md). Two namespace
rules to know:

- Agent-facing JSON reads live under `/api/...` (`/api/students`,
  `/api/students/{id}`, `/api/cohorts/{id}`, `/api/cohorts/{id}/outcomes`).
- The bare `/students/{id}` route is the director-facing Jinja profile page.
  Don't reuse that path for JSON.

## Testing

- `tests/test_services.py` covers domain behavior and edge cases.
- `tests/test_app.py` covers API contracts.
- `tests/test_ui.py` verifies static UI serving.
- `tests/test_e2e.py` launches Uvicorn and drives Chromium through common and edge-case workflows.

## Design Principles

- API-first: the UI should call the same endpoints external systems use.
- Explainable defaults: service outputs include reasons or effectiveness labels.
- Contributor simplicity: no frontend build chain until the project truly needs one.
- Testable units: business behavior belongs in small service functions.
