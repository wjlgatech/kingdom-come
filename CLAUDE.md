# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Required reading before UI / product work

- `DESIGN.md` — fonts, color tokens, spacing, motion, component primitives, and the "Editorial Pastoral" aesthetic. Do not deviate without explicit user approval; in QA / design-review mode, flag any UI code that doesn't match it.
- `COMPETITIVE-UX.md` — the 8 prioritized recommendations (REC-1…REC-8) and the 5 user stories (Marcus #1–#2, Sister Theresa #3–#5). When proposing UI work, anchor changes to a specific REC and a specific story.

## Commands

```bash
# 1-click install + stand up (demo seed + free-LLM chain auto-detected)
./run.sh

# One-time dev setup (tests need the dev extras + Playwright)
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

# Run with seeded prayer/prophecy demo data (opt-in; tests rely on empty ledgers)
KC_DEMO_SEED=1 uvicorn backend.app:app --reload

# Container (verified): demo mode out of the box — see docs/DEPLOY.md
docker compose up --build
```

## Architecture

FastAPI monolith serving JSON endpoints **and** server-rendered Jinja pages for a vanilla-JS frontend. No build chain.

- `backend/app.py` — single source of truth for routes, request schemas, subnav wiring (`SEMINARIAN_SUBNAV` / `DIRECTOR_SUBNAV`), and Jinja template rendering. Static assets are mounted at `/static` from `frontend/`.
- `backend/services/` — pure domain functions; this is where business behavior lives and where new tests should be anchored. `predictive.dropout_risk`, `curriculum.recommend_content`, and `orchestration.class_orchestrator` are deliberately small and synchronous.
- `backend/api/ws_chat.py` + `backend/services/ai_pipeline.py` — the streaming mentor chat. The WS contract: yield `{"memory": [...]}` **first** so the UI can render "Mentor remembers:" pills, then stream `{"chunk": "..."}` messages, then `{"done": true}`. Errors come back as `{"error": "..."}` without closing the socket. Don't reorder these.
- `backend/services/stt.py` + `/api/voice/{health,transcribe}` — voice input (mic on `/me/chat` + the Copilot panel, shared `frontend/voice.js`). Chain: `VOICE_FAKE_TEXT` → faster-whisper (`.[voice]` extra) → OpenAI Whisper → unavailable (UI hides the mic via the health probe). Raw-body upload (no python-multipart dep). Never persist or log audio.
- `backend/api/ws_copilot.py` + `backend/services/copilot.py` — the in-app Copilot (`Ask ✦` on `/me`, `/cohort`, `/cohort/triage`; shared `frontend/copilot.{js,css}`). Same contract family: `{"context": [tool names]}` first, then chunks, then done. Gather-then-ground: all role-scoped tools run in-process, one completion streams over them; with `LLM_FAKE_RESPONSE` set it emits a deterministic grounded digest (true numbers) instead of the canned line. **Privacy by construction:** the director scope never receives a `student_id` and cannot reach ledger content; the seminarian scope reads only the asker's record. `copilot._STATUS_BY_SCORE`/`_REASON_TEXT` mirror `frontend/status.js` — keep them in sync.
- `backend/services/vector_memory.py` — per-student in-process FAISS index keyed by `student_id`. State persists for the lifetime of the process; tests must call `vector_memory.reset()` between cases. Embeddings come from OpenAI when `OPENAI_API_KEY` is set, otherwise a deterministic hash-bucket fake (`EMBEDDING_FAKE=1` forces the fake even when a key is present).
- `backend/services/llm_client.py` — mentor backend is a **fallback chain** (`resolve_chain()`, unit-tested in `tests/test_llm_client.py`): `LLM_FAKE_RESPONSE` short-circuits (every E2E test) → NVIDIA NIM (free; default `openai/gpt-oss-120b` — kimi-k2.6 leaks reasoning into `delta.content`, glm-5.1 is ~35s to first token) → local Ollama (always wired, `qwen2.5:7b`) → OpenRouter → OpenAI. Failure before first chunk advances the chain; mid-stream failure re-raises (never splice two providers' text). `LLM_MODEL` overrides the primary tier only. Sampling is pinned (`temperature=0.6`, `max_tokens=400`).
- `backend/services/realtime.py` — Redis pub/sub for activity events. Falls back to `fakeredis` when `REDIS_URL` is unset. Tests must call `realtime.reset_for_tests()` between cases.
- `backend/services/journey.py` — the shared 40-day journey (C4): stateless, day derived from `KC_JOURNEY_START`; `GET /api/journey`. `backend/services/pulse.py` — the director's weekly pulse note (C5): one LLM-composed paragraph from **counts-only** aggregates; the prompt must never see names or ledger content (`tests/test_journey_pulse.py` enforces this).
- Mentor memory is user-controlled (REC-3): `GET /api/memory/{student_id}` + `DELETE /api/memory/{student_id}/{index}` over `vector_memory.list_memories` / `delete_memory` (FAISS index rebuilds on delete); "Manage memory" modal on `/me/chat`.
- Roster CSV import: `POST /api/cohorts/{id}/import` → `cohort_fixtures.import_cohort_csv` (all-or-nothing; `reset_cohort()` restores the shipped roster between tests).
- `backend/db/connection.py` + `backend/models/outcome.py` — SQLAlchemy 2.x `DeclarativeBase`. `init_db()` is opt-in; the running app does not auto-create tables. `DATABASE_URL` defaults to `sqlite:///./formation.db`.

### Two product surfaces share one backend

1. **Redesigned per-persona surfaces** (the real product, anchored to the user stories): `/` (door), `/me`, `/me/chat`, `/me/prayer`, `/me/timeline`, `/me/year` (Formation Year annual spread), `/cohort`, `/cohort/triage`, `/cohort/groups`, `/students/{id}`. Each Jinja page extends `frontend/_base.html`, sets `required_role` (the base template's role gate reads this), and ships its own `*.css` + `*.js` files. Role + student id are persisted in `localStorage` (`kc-role`, `kc-student-id`) by the door page's inline script; first-run tours use `kc-tour-me` / `kc-tour-cohort` (`frontend/tour.js`, and E2E tests pre-dismiss them in `_seed_role`).
2. **Admin workbench** at `/admin/workbench` (serves `frontend/index.html`) — the original endpoint-shaped form playground. Kept for engineers / API debugging; do not regress it but do not extend it.

### Prayer + prophecy ledgers

- `backend/services/prayer.py` is the in-process domain layer for two parallel ledgers: a **prayer ledger** (petition → intercessions → answer with structured status `answered_yes/partial/no/superseded` + testimony) and a **prophecy ledger** (word → 2-of-3 weighing per 1 Cor 14:29 → confirmed/refined/rejected → fulfillment with status `fulfilled/partial/unfulfilled`).
- Visibility model is the same for both: `private` / `small_group` (speaker designates recipient peers explicitly — no persistent small-group entity) / `cohort`. The `visible_to` filter on `list_*` enforces the policy.
- The 2-of-3 rule lives in `_resolve_prophecy_status`. Submission requires 3 distinct weighers; the speaker cannot weigh their own word; weighers can only weigh once. Two confirms lock to `confirmed`; two rejects to `rejected`; any `refine` after a second judgment moves to `refined`.
- Cohort-level **tradition policy** (`catholic` default, `charismatic` opt-in) is stored at `_state["policies"]` and exposed at `/api/cohorts/{id}/policy`. Same data model serves both traditions; the flag flips defaults and (eventually) UI copy.
- State is in-process (`prayer._state`); tests must call `prayer.reset()` between cases. **Opt-in persistence** (`KC_PERSIST=1`): every mutation write-through upserts a JSON row (`backend/models/ledger.py`, table `ledger_records`) and startup replays rows via `prayer.enable_persistence()` — in-memory stays the read path and the test default. Run exactly one process/machine when enabled (states diverge otherwise; see `docs/DEPLOY.md`).
- **UI:** seminarians work both ledgers at `/me/prayer` (`frontend/prayer.{html,css,js}` — tabs: My prayers / Words / To weigh; pastoral status labels live in `prayer.js`, e.g. `rejected` renders as "Not confirmed"). Directors get a counts-only rhythm section + tradition toggle on `/cohort` and a counts-only line on `/students/{id}` — never ledger content.
- `prayer.seed_demo()` populates an idempotent demo week; the app calls it only when `KC_DEMO_SEED=1` (tests and fresh API consumers must start empty).
- Track records: `prayer_track_record(student_id)` returns counts + answer rate; `prophecy_track_record(speaker_id)` returns counts + confirmation rate + fulfillment rate. `cohort_rhythm(student_ids)` is the director-facing aggregate — counts only, never content.
- Endpoints at `/api/prayer/...` and `/api/prophecies/...` (note: the prophecy collection is at `/api/prophecies`, not `/api/prayer/prophecies`, because prophecy is a peer ledger, not a sub-resource of prayer). Track records at `/api/prayer/track-record/{student_id}` and `/api/cohorts/{id}/prayer-rhythm`.
- 11 MCP tools wrap these endpoints (see `mcp_server/server.py`).

### Agent integration (MCP)

- `mcp_server/server.py` exposes 20 tools over stdio via `FastMCP` (`mcp` SDK 1.x): the original 9 (`dropout_risk`, `curriculum_recommend`, `orchestration_plan`, `log_outcome`, `list_students`, `get_student`, `get_cohort`, `list_cohort_outcomes`, `chat_with_mentor`) plus 11 prayer/prophecy tools (`submit_prayer_request`, `list_prayer_requests`, `mark_prayer_answered`, `add_intercession`, `submit_prophecy`, `weigh_prophecy`, `record_prophecy_fulfillment`, `list_prophecies`, `get_prayer_track_record`, `get_cohort_prayer_rhythm`, `set_cohort_tradition`). Tools are thin `httpx` wrappers over the FastAPI; `chat_with_mentor` opens the WS, drains `memory + chunks + done`, and returns the whole reply (no streaming through MCP).
- Configure via env: `KC_BASE_URL` (default `http://127.0.0.1:8000`), `KC_WS_URL` (derived if unset), `KC_TIMEOUT_S` (default 30). For offline agent demos use the same `EMBEDDING_FAKE=1` + `LLM_FAKE_RESPONSE=...` env vars the E2E tests use.
- Agent-facing read endpoints live under **`/api/...`** (e.g. `/api/students/{id}`) so they don't collide with the Jinja page route at `/students/{id}`. When adding new agent reads, keep the namespace.
- Cohort/student data has a **single source of truth**: `backend/fixtures/cohort.py`. The frontend fetches it — `frontend/cohort_data.js` is an API-backed module (top-level await over `/api/students`; async `getProfile()` over `/api/students/{id}`) that keeps the old export interface. Do not reintroduce a static roster copy.
- `.claude-plugin/plugin.json` registers the MCP server with Claude Code; `docs/AGENTS.md` has the wiring snippets for Claude Code, Codex, Hermes, and other MCP-aware harnesses.
- **Journey skills** live in `skills/` (`morning-check-in`, `cohort-triage`, `prayer-ledger`) — harness-neutral playbooks that give agents the webapp's role-shaped UX over the MCP tools. If you change status vocabulary, reason translations, or ledger guardrails, update the skills too.

### Deployment

- `Dockerfile` (verified: build + run + smoke), `docker-compose.yml` (demo mode), `render.yaml`, `fly.toml`, guide in `docs/DEPLOY.md`. The image installs `.[standalone]` because `realtime.py` imports `fakeredis` when `REDIS_URL` is unset.
- `LLM_FAKE_RESPONSE` takes precedence over `OPENAI_API_KEY` in `llm_client.py` — switching a deployment to the real mentor means removing the fake var, not just adding the key.

### Frontend conventions

- All interactive elements addressable from tests via `data-testid` (see `tests/test_routes.py::test_per_page_assets_are_referenced` for the canonical list of per-page asset pairs).
- Never let raw status codes leak into the UI. The mapping `low_engagement` / `few_reflections` / `calling_drift` → plain-English sentence and `dropout_risk` score → `Thriving` / `Steady` / `Needs check-in` / `At risk` lives in `frontend/status.js` (`statusFromRisk`, `reasonsToSentence`). `tests/test_e2e_kc.py::test_e2e_triage_renders_named_statuses_with_reasons` enforces this.
- Status is never communicated by color alone (REC-2 + accessibility floor in `DESIGN.md`).
- Data containers that fill from JS start `aria-busy="true"` + `data-skeleton` in the HTML; a shared rule in `components.css` renders pulsing placeholders until the page's JS clears/falsifies `aria-busy` (every path — success, empty, and error — must do so, or the skeleton pulses forever).
- Client-side risk scoring goes through `frontend/cohort_risk.js` (`scoreStudent` / `countFlagged`) — never duplicate the override weighting; the door previews and triage share it, and `backend/services/pulse.py` mirrors it server-side.
- Accessibility is a test, not a hope: `tests/test_a11y.py` runs vendored axe-core (`tests/vendor/axe.min.js`) over all primary surfaces; serious/critical WCAG A/AA violations fail the build. New text/background color pairs must clear 4.5:1 (the tokens were fixed once already — don't reintroduce `#8a8378`-class contrast).
- PWA shell: `frontend/manifest.json` + `frontend/sw.js` (served at `/sw.js` from root for scope; caches `/static/*` only — pages/API must stay network-only). The persona subnav docks to the bottom edge under 640px.

### Testing conventions

- Playwright fixtures (`tests/test_e2e.py`, `tests/test_e2e_kc.py`) start uvicorn on a free port with `EMBEDDING_FAKE=1` + `LLM_FAKE_RESPONSE=...` and pop `REDIS_URL`. Reuse this pattern for new E2E tests.
- For role-gated pages, seed `localStorage` before navigating (see `_seed_role` in `tests/test_e2e_kc.py`) — direct visits otherwise hit the role-gate banner.
- **Race-flake lesson (commit 3087bda, called out in `tests/test_e2e_kc.py` docstring):** assert against actual DOM content with `page.wait_for_function(...)`. Never `wait_for()` on an already-visible element.
- Unit tests that touch chat / memory / events must use the `isolated_state` fixture pattern (`tests/test_ai_pipeline.py`, `tests/test_ws_chat.py`) — process-global FAISS + Redis state will leak across tests otherwise.
