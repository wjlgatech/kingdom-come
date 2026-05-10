# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Required reading before UI / product work

- `DESIGN.md` — fonts, color tokens, spacing, motion, component primitives, and the "Editorial Pastoral" aesthetic. Do not deviate without explicit user approval; in QA / design-review mode, flag any UI code that doesn't match it.
- `COMPETITIVE-UX.md` — the 8 prioritized recommendations (REC-1…REC-8) and the 5 user stories (Marcus #1–#2, Sister Theresa #3–#5). When proposing UI work, anchor changes to a specific REC and a specific story.

## Commands

```bash
# One-time setup
python -m venv .venv && source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m playwright install chromium

# Run the app (UI at http://127.0.0.1:8000, OpenAPI at /docs)
uvicorn backend.app:app --reload

# Full test suite (unit + API + WS + Playwright E2E)
python -m pytest

# Single test file or single test
python -m pytest tests/test_routes.py
python -m pytest tests/test_e2e_kc.py::test_e2e_chat_streams_reply_and_renders_memory_pills_on_second_send

# Skip the slow Playwright suites while iterating on backend
python -m pytest --ignore=tests/test_e2e.py --ignore=tests/test_e2e_kc.py

# Syntax sanity check used in the README's "Test Matrix"
python -m compileall backend tests
```

## Architecture

FastAPI monolith serving JSON endpoints **and** server-rendered Jinja pages for a vanilla-JS frontend. No build chain.

- `backend/app.py` — single source of truth for routes, request schemas, subnav wiring (`SEMINARIAN_SUBNAV` / `DIRECTOR_SUBNAV`), and Jinja template rendering. Static assets are mounted at `/static` from `frontend/`.
- `backend/services/` — pure domain functions; this is where business behavior lives and where new tests should be anchored. `predictive.dropout_risk`, `curriculum.recommend_content`, and `orchestration.class_orchestrator` are deliberately small and synchronous.
- `backend/api/ws_chat.py` + `backend/services/ai_pipeline.py` — the streaming mentor chat. The WS contract: yield `{"memory": [...]}` **first** so the UI can render "Mentor remembers:" pills, then stream `{"chunk": "..."}` messages, then `{"done": true}`. Errors come back as `{"error": "..."}` without closing the socket. Don't reorder these.
- `backend/services/vector_memory.py` — per-student in-process FAISS index keyed by `student_id`. State persists for the lifetime of the process; tests must call `vector_memory.reset()` between cases. Embeddings come from OpenAI when `OPENAI_API_KEY` is set, otherwise a deterministic hash-bucket fake (`EMBEDDING_FAKE=1` forces the fake even when a key is present).
- `backend/services/llm_client.py` — set `LLM_FAKE_RESPONSE="..."` to bypass OpenAI; the fake streams the string word-by-word. Used by every E2E test.
- `backend/services/realtime.py` — Redis pub/sub for activity events. Falls back to `fakeredis` when `REDIS_URL` is unset. Tests must call `realtime.reset_for_tests()` between cases.
- `backend/db/connection.py` + `backend/models/outcome.py` — SQLAlchemy 2.x `DeclarativeBase`. `init_db()` is opt-in; the running app does not auto-create tables. `DATABASE_URL` defaults to `sqlite:///./formation.db`.

### Two product surfaces share one backend

1. **Redesigned per-persona surfaces** (the real product, anchored to the user stories): `/` (door), `/me`, `/me/chat`, `/me/timeline`, `/cohort`, `/cohort/triage`, `/cohort/groups`, `/students/{id}`. Each Jinja page extends `frontend/_base.html`, sets `required_role` (the base template's role gate reads this), and ships its own `*.css` + `*.js` files. Role + student id are persisted in `localStorage` (`kc-role`, `kc-student-id`) by `door.js`.
2. **Admin workbench** at `/admin/workbench` (serves `frontend/index.html`) — the original endpoint-shaped form playground. Kept for engineers / API debugging; do not regress it but do not extend it.

### Prayer + prophecy ledgers

- `backend/services/prayer.py` is the in-process domain layer for two parallel ledgers: a **prayer ledger** (petition → intercessions → answer with structured status `answered_yes/partial/no/superseded` + testimony) and a **prophecy ledger** (word → 2-of-3 weighing per 1 Cor 14:29 → confirmed/refined/rejected → fulfillment with status `fulfilled/partial/unfulfilled`).
- Visibility model is the same for both: `private` / `small_group` (speaker designates recipient peers explicitly — no persistent small-group entity) / `cohort`. The `visible_to` filter on `list_*` enforces the policy.
- The 2-of-3 rule lives in `_resolve_prophecy_status`. Submission requires 3 distinct weighers; the speaker cannot weigh their own word; weighers can only weigh once. Two confirms lock to `confirmed`; two rejects to `rejected`; any `refine` after a second judgment moves to `refined`.
- Cohort-level **tradition policy** (`catholic` default, `charismatic` opt-in) is stored at `_state["policies"]` and exposed at `/api/cohorts/{id}/policy`. Same data model serves both traditions; the flag flips defaults and (eventually) UI copy.
- State is in-process (`prayer._state`); tests must call `prayer.reset()` between cases. Persistence (SQLAlchemy-backed) is the natural next step but matches the existing in-memory-first pattern of `vector_memory` / `realtime`.
- Track records: `prayer_track_record(student_id)` returns counts + answer rate; `prophecy_track_record(speaker_id)` returns counts + confirmation rate + fulfillment rate. `cohort_rhythm(student_ids)` is the director-facing aggregate — counts only, never content.
- Endpoints at `/api/prayer/...` and `/api/prophecies/...` (note: the prophecy collection is at `/api/prophecies`, not `/api/prayer/prophecies`, because prophecy is a peer ledger, not a sub-resource of prayer). Track records at `/api/prayer/track-record/{student_id}` and `/api/cohorts/{id}/prayer-rhythm`.
- 11 MCP tools wrap these endpoints (see `mcp_server/server.py`).

### Agent integration (MCP)

- `mcp_server/server.py` exposes 20 tools over stdio via `FastMCP` (`mcp` SDK 1.x): the original 9 (`dropout_risk`, `curriculum_recommend`, `orchestration_plan`, `log_outcome`, `list_students`, `get_student`, `get_cohort`, `list_cohort_outcomes`, `chat_with_mentor`) plus 11 prayer/prophecy tools (`submit_prayer_request`, `list_prayer_requests`, `mark_prayer_answered`, `add_intercession`, `submit_prophecy`, `weigh_prophecy`, `record_prophecy_fulfillment`, `list_prophecies`, `get_prayer_track_record`, `get_cohort_prayer_rhythm`, `set_cohort_tradition`). Tools are thin `httpx` wrappers over the FastAPI; `chat_with_mentor` opens the WS, drains `memory + chunks + done`, and returns the whole reply (no streaming through MCP).
- Configure via env: `KC_BASE_URL` (default `http://127.0.0.1:8000`), `KC_WS_URL` (derived if unset), `KC_TIMEOUT_S` (default 30). For offline agent demos use the same `EMBEDDING_FAKE=1` + `LLM_FAKE_RESPONSE=...` env vars the E2E tests use.
- Agent-facing read endpoints live under **`/api/...`** (e.g. `/api/students/{id}`) so they don't collide with the Jinja page route at `/students/{id}`. When adding new agent reads, keep the namespace.
- Cohort/student data comes from `backend/fixtures/cohort.py`, ported from `frontend/cohort_data.js`. The two are duplicated source-of-truth until the frontend migrates to fetch `/api/students` — keep them in sync until then.
- `.claude-plugin/plugin.json` registers the MCP server with Claude Code; `docs/AGENTS.md` has the wiring snippets for Claude Code, Codex, and other MCP-aware harnesses.

### Frontend conventions

- All interactive elements addressable from tests via `data-testid` (see `tests/test_routes.py::test_per_page_assets_are_referenced` for the canonical list of per-page asset pairs).
- Never let raw status codes leak into the UI. The mapping `low_engagement` / `few_reflections` / `calling_drift` → plain-English sentence and `dropout_risk` score → `Thriving` / `Steady` / `Needs check-in` / `At risk` lives in `frontend/status.js` (`statusFromRisk`, `reasonsToSentence`). `tests/test_e2e_kc.py::test_e2e_triage_renders_named_statuses_with_reasons` enforces this.
- Status is never communicated by color alone (REC-2 + accessibility floor in `DESIGN.md`).

### Testing conventions

- Playwright fixtures (`tests/test_e2e.py`, `tests/test_e2e_kc.py`) start uvicorn on a free port with `EMBEDDING_FAKE=1` + `LLM_FAKE_RESPONSE=...` and pop `REDIS_URL`. Reuse this pattern for new E2E tests.
- For role-gated pages, seed `localStorage` before navigating (see `_seed_role` in `tests/test_e2e_kc.py`) — direct visits otherwise hit the role-gate banner.
- **Race-flake lesson (commit 3087bda, called out in `tests/test_e2e_kc.py` docstring):** assert against actual DOM content with `page.wait_for_function(...)`. Never `wait_for()` on an already-visible element.
- Unit tests that touch chat / memory / events must use the `isolated_state` fixture pattern (`tests/test_ai_pipeline.py`, `tests/test_ws_chat.py`) — process-global FAISS + Redis state will leak across tests otherwise.
