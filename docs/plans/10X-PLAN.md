# 10X Plan — Kingdom Come

*Drafted 2026-07-03 via `/anyagent goal`. Anchored to `COMPETITIVE-UX.md` (REC-1…8, stories #1–#5),
`ROADMAP.md`, and `DESIGN.md` ("Editorial Pastoral"). Baseline: 120 tests green, OOP score 63/100,
all P1/P2 surfaces shipped, `./run.sh` 1-click stand-up, verified Docker + Render/Fly blueprints.*

The plan has three pillars, each answering one clause of the objective:
**A. one-click downloadable** · **B. smooth the experience** · **C. create wow**.
Each item states the plain idea, then pins the exact handle an engineer needs.

---

## Pillar A — One-click downloadable (from "clone + run" to "click + use")

Today the smallest path is `git clone` + `./run.sh`. That's one *command*, not one *click*.
Ranked by reach-per-effort:

| # | Move | What the user does | Exact handle | Effort |
|---|------|--------------------|--------------|--------|
| A1 | **Hosted demo** (already "Next" on the roadmap) | Clicks a URL. Nothing to install. | `render.yaml` / `fly.toml` are ready; needs a platform account. Set `KC_DEMO_SEED=1`, `EMBEDDING_FAKE=1`, and a free `NVIDIA_API_KEY` (see `docs/DEPLOY.md`). | S — configs verified |
| A2 | **Deploy-to-Render / Fly buttons in README** | Clicks a badge, gets their own instance. | Add `https://render.com/deploy?repo=…` button to `README.md` Quickstart; `render.yaml` already defines the service. | S |
| A3 | **`uvx kingdom-come`** — PyPI package with a console script | One command, no clone, no venv thinking. | Add `[project.scripts] kingdom-come = "backend.cli:main"` to `pyproject.toml`; a ~20-line `backend/cli.py` that wraps `uvicorn.run("backend.app:app")` with the same env-defaults logic as `run.sh` (port, `KC_DEMO_SEED`, NIM key pickup). Publish via a `release.yml` GitHub Action. | M |
| A4 | **Published container image** | `docker run -p 8000:8000 ghcr.io/wjlgatech/kingdom-come` | `Dockerfile` is verified; add a GH Action pushing to GHCR on tag. Compose stays for local dev. | S |
| A5 | **Downloadable release bundle** (true double-click for macOS) | Downloads a `.zip` from GitHub Releases, double-clicks `Kingdom Come.command`. | A 5-line `.command` wrapper that `cd`s to the bundle and executes `run.sh` (which already self-installs a venv via uv/python3.11+). | S |

**Order:** A1 → A2 → A4 → A3 → A5. A1 is the 10X: the truest one-click is zero installs,
and every marketing surface can then link a live instance.

## Pillar B — Smooth the experience (friction kill-list)

| # | Friction today | Fix | Exact handle | Effort |
|---|----------------|-----|--------------|--------|
| B1 | **Ledgers evaporate on restart** — prayers/prophecies are in-process (`prayer._state`), so a redeploy erases a user's track record. The single biggest real-user trust breach. | SQLAlchemy persistence behind the same function signatures; keep in-memory as the test default. | `backend/services/prayer.py` (+ `vector_memory.py` later); models beside `backend/models/outcome.py`; `init_db()` in `backend/db/connection.py` is already opt-in. Roadmap "Next" item. | M-L |
| B2 | **First-run intuition gap** (anti-pattern AP4 — Hallow needed an external "how to" page) | 3-step inline tour on first visit of each role home: seminarian (`/me`) and director (`/cohort`), dismissible, stored in `localStorage` (`kc-tour-done`). Door cards preview what's behind them (REC-1 refinement: "2 students need a check-in this week"). | `frontend/door.js` + `me.js` / `cohort.js`; content from live `/api/...` calls, not hardcoded. | S-M |
| B3 | **No phone-shaped experience** — formation happens in chapels and hallways, not at desks | PWA: `manifest.json` + minimal service worker → "Add to Home Screen", plus bottom-nav on small viewports (Hallow's thumb-reach pattern, `DESIGN.md` breakpoints). | Serve manifest from `frontend/`; register in `frontend/_base.html`; media-query nav in `_base` CSS. | M |
| B4 | **Cohort data is fixture-only** — a real director can't load *her* 24 students | CSV import (roadmap "Next"): upload on `/cohort` → POST `/api/cohorts/{id}/import` → replaces the fixture roster for the session. | New route in `backend/app.py`, service fn in `backend/services/`, single source of truth stays `backend/fixtures/cohort.py` shape. | M |
| B5 | **Perceived latency on data pages** | Skeleton placeholders while `cohort_data.js` awaits `/api/students` (it top-level-awaits today, blanking the pane). | Per-page CSS skeletons; keep `data-testid` contracts (`tests/test_routes.py::test_per_page_assets_are_referenced`). | S |
| B6 | **Accessibility floor unverified** (roadmap "Next") | axe-core pass in Playwright as a test, fixing what it finds; status already never color-alone (REC-2). | New `tests/test_a11y.py` reusing the E2E fixture pattern (`EMBEDDING_FAKE=1`, `LLM_FAKE_RESPONSE`). | M |

## Pillar C — Create wow (moments users retell)

Ordered by wow-per-effort; every one keeps the Editorial Pastoral register (subtle > flashy).

1. **"Answered" moments** — when a petition is marked `answered_yes`, the ledger doesn't just
   update a row: a quiet testimony card composes itself ("Asked June 3 · Carried by 2 peers ·
   Answered July 1") with a slow-fade gold hairline, and the answer rate ticks up in the
   track-record header. *Handle:* `frontend/prayer.js` render path for `mark_answered`;
   data already in `prayer_track_record()`. **Effort S.**
2. **The Formation Year** — a Wrapped-style annual page: your reflections, answered prayers,
   confirmed words, curriculum arc, rendered as an editorial spread (Fraunces display type,
   print-quality). Nobody in the category does longitudinal narrative (COMPETITIVE-UX
   "unpopulated space"). *Handle:* new `/me/year` Jinja page over `prayer_track_record`,
   `list_outcomes`, timeline data; roadmap "Later — longitudinal analytics" pulled forward.
   **Effort M.**
3. **Editable mentor memory** — "Mentor remembers" pills become manageable: view, delete
   (ChatGPT transparency pattern; Pi's opacity is cited as its regression). *Handle:*
   `vector_memory.py` needs `delete(student_id, idx)`; small `/api/memory` routes; pills UI
   already in `chat.js`. **Effort S-M.**
4. **The 40-day shared journey** (REC-8) — "Advent journey" wrapper: cohort + deadline as the
   engagement engine (Hallow's Pray 40). Day-counter on `/me`, cohort completion pulse on
   `/cohort`. *Handle:* thin service over existing curriculum + outcomes; no new data model
   needed for v1. **Effort M.**
5. **Weekly cohort pulse note** — Monday morning, Theresa opens `/cohort` to one composed
   paragraph: "Three students are carrying heaviness this week; the cohort's prayer rhythm
   deepened…" — LLM-written from counts-only aggregates (never ledger content; visibility
   model in `prayer.py` already enforces this). *Handle:* `llm_client.stream_chat` over
   `cohort_rhythm()` + `dropout_risk` outputs. **Effort M.**
6. **Agents as another door** — demo video + README section: Claude/Hermes running
   `morning-check-in` against the same instance a human uses (`skills/`, 20 MCP tools already
   shipped). The wow is *parity*: your agent sees your formation world. **Effort S (packaging
   what exists).**

## Sequencing

- **Wave 1 (this week, all S):** A1 hosted demo + A2 README buttons + C1 answered-moments + B5 skeletons.
- **Wave 2 (next 2–3 weeks):** B1 persistence (prerequisite for any real user), B2 onboarding, C3 editable memory, A4 GHCR image.
- **Wave 3 (the month after):** C2 Formation Year, B3 PWA, B4 CSV import, C4 40-day journey, A3 PyPI, C5 pulse note, B6 a11y.

**The 10X thesis in one sentence:** persistence (B1) + a hosted demo (A1) turn this from a
verified local demo into a product a stranger can use tonight; the Formation Year (C2) and
answered-moments (C1) turn usage into stories people retell — and retold stories, not
features, are the 10X.
