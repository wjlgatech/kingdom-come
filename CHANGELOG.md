# Changelog

All notable changes to Kingdom Come are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- **The Copilot door (`Ask ✦`)** — an on-page agent on `/me`, `/cohort`, and
  `/cohort/triage` (agentic-portfolio pattern): ask a question, and the
  answer is composed from the app's *own live tools*, with "Consulted:"
  pills showing exactly what was read. Gather-then-ground architecture
  (`backend/services/copilot.py` + `/ws/copilot`, same frame contract family
  as `/ws/chat`: context → chunks → done): every tool in the asker's role
  scope runs in-process, then one completion streams through the mentor's
  survival chain — and with **no model attached, a deterministic grounded
  digest answers with true numbers** (keyless demos stay functional).
  Role-scoped privacy by construction: the director scope is
  names/statuses/counts and can never reach ledger content; the seminarian
  scope is the asker's own record only (`tests/test_copilot.py` enforces
  both). *Why:* the northstar — agents as another door into the same room —
  now includes the room itself.

### Fixed

- **E2E server freeze at ~18 tests** — the `live_app` fixtures piped uvicorn's
  stdout and never drained it, so the access log filled the 64KB pipe buffer
  and the blocked log write froze the whole server (`Page.goto` timeouts that
  looked like order-dependent flake). Both fixtures now use `DEVNULL`, matching
  `tests/test_a11y.py`; diagnosed by curling the test server from outside
  during the hang (reset → refused = server-side, not browser-side).

## [0.9.0] - 2026-07-03

### Added

- **Answered-prayer moment on `/me/prayer`** (10X plan C1) — a resolved
  petition now composes its whole journey as an "answered arc" line
  ("Asked … · Carried by N peers · Answered …", `data-testid`
  `prayer-answered-arc`), and marking a petition `answered_yes` plays one
  quiet thriving-toned reveal on the card (`--motion-long`, collapses under
  `prefers-reduced-motion`). *Why:* the ledger's payoff moment was a silent
  row update; retold moments are the engagement engine.
- **Loading skeletons on data pages** (10X plan B5) — containers that start
  `aria-busy="true"` (`cohort overview snippets, triage list, timeline,
  the three prayer ledgers`) now show two pulsing placeholder cards via a
  shared `[data-skeleton]` rule in `components.css` until their JS clears
  the attribute. *Why:* `cohort_data.js` top-level-awaits `/api/students`,
  which left these panes blank during load.
- **One-click deploy buttons** (10X plan A2) — Deploy-to-Render button in
  `README.md` and `docs/DEPLOY.md` (the repo is public; `render.yaml` drives
  it) plus the `fly launch --copy-config --now` one-liner.
- **Hosted demo live at https://kingdom-come.fly.dev** (10X plan A1) —
  deployed from the shipped `fly.toml` (demo mode, zero secrets, scales to
  zero when idle) and smoke-checked live: `/health` 200, both role doors,
  `/api/students`, seeded prayer ledger, OpenAPI at `/docs`, and the mentor
  WS contract (memory → chunks → done) end to end.
- **`docs/plans/10X-PLAN.md`** — the 10X improvement plan: one-click
  distribution (hosted demo, deploy buttons, `uvx`, GHCR image), the UX
  friction kill-list (persistence first), and six "wow" moments, sequenced in
  three waves and anchored to `COMPETITIVE-UX.md` REC-1…8.
- **Ledger persistence (`KC_PERSIST=1`)** (10X plan B1) — the prayer +
  prophecy ledgers survive restarts/redeploys: every mutation write-through
  upserts a JSON row (`backend/models/ledger.py`, one `ledger_records`
  table), and startup replays rows into the in-process state
  (`prayer.enable_persistence()`). Opt-in, so tests and default runs keep the
  in-memory-only behavior; verified live with a real uvicorn restart. *Why:*
  a track record that resets on redeploy breaks the product's core promise.
- **First-run tour + live door previews** (10X plan B2, anti-pattern AP4) —
  `/me` and `/cohort` show a quiet three-step tour on first visit (shared
  `frontend/tour.js`, dismissal persists in `localStorage` `kc-tour-*`), and
  the door cards now preview live data: the director card swaps in the real
  "N students need a check-in" count, the seminarian card the real next
  curriculum step. Scoring extracted to `frontend/cohort_risk.js` so the
  door and triage share one path.
- **User-controlled mentor memory** (10X plan C3, REC-3) — "Manage memory"
  on `/me/chat` (previously a disabled placeholder) opens the list of what
  the mentor remembers with per-item Forget; backed by
  `GET /api/memory/{student_id}` + `DELETE /api/memory/{student_id}/{index}`
  (`vector_memory.list_memories` / `delete_memory`, FAISS index rebuilt on
  delete).
- **GHCR image workflow** (10X plan A4) — `.github/workflows/publish-image.yml`
  publishes `ghcr.io/wjlgatech/kingdom-come` (`:latest` on main, semver on
  tags). Not yet verified — it runs on the next push to main.
- **The Formation Year at `/me/year`** (10X plan C2) — an editorial annual
  spread assembled from the student's own record: numbers row (reflections,
  petitions, answered, outcomes), reflection lines as quotes, answered
  petitions with testimonies, and the weekly status arc. New "Year" subnav
  entry. *Why:* the longitudinal-narrative space no competitor touches
  (`COMPETITIVE-UX.md` "unpopulated space").
- **`uvx` / PyPI packaging** (10X plan A3) — dist renamed `kingdom-come`
  with a `kingdom-come` console script (`backend/cli.py`, demo-first
  defaults); the wheel now ships the frontend as a `frontend` package and
  `app.py` falls back to `importlib.resources`, verified by installing the
  wheel in a clean venv and serving pages from site-packages. Works today:
  `uvx --from git+https://github.com/wjlgatech/kingdom-come kingdom-come`.
  PyPI publish workflow (`publish-pypi.yml`) is trusted-publishing-ready but
  blocked on one-time PyPI project setup.
- **CSV cohort import** (10X plan B4) — `POST /api/cohorts/{id}/import`
  (header `id,name,engagement,reflection_count,calling`, `;`-separated
  callings, Excel-BOM tolerant, all-or-nothing validation) +
  "Import roster (CSV)" on `/cohort`. `cohort_fixtures.reset_cohort()`
  restores the shipped roster.
- **Forty Days of Discernment** (10X plan C4, REC-8) — a shared 40-day
  journey (`backend/services/journey.py`, stateless: the day derives from
  `KC_JOURNEY_START`) surfaced as a day line on `/me` and `/cohort`, via
  `GET /api/journey`.
- **Weekly cohort pulse note** (10X plan C5) — `GET
  /api/cohorts/{id}/pulse-note` composes one pastoral paragraph through the
  mentor LLM chain from counts-only aggregates (`backend/services/pulse.py`;
  the prompt never sees names or ledger content — tested), rendered
  additively under the stats sentence on `/cohort`.
- **PWA + thumb-reach nav** (10X plan B3) — installable app shell
  (`manifest.json`, `icon.svg`, `/sw.js` served from root scope; the worker
  caches `/static/*` only, pages and API stay network-only), and the persona
  subnav docks to the bottom edge under 640px.
- **Accessibility audit as a test** (10X plan B6) — `tests/test_a11y.py`
  runs vendored axe-core 4.10.2 over all ten primary surfaces; serious or
  critical WCAG A/AA violations fail the build.

### Fixed

- **AA contrast on `--ink-faint` and light-mode `--status-checkin`** — the
  axe audit caught both failing the 4.5:1 floor `DESIGN.md` claims
  (`#8a8378` ≈ 3.5:1, amber `#b88a1f` ≈ 2.7:1 on its soft chip). Now
  `#736c60` / `#9a9184` (dark) and `#7f5f0d`; `DESIGN.md` palette updated to
  match reality.
- **`/me` "View full arc" button** was still a disabled "Coming soon"
  placeholder although `/me/timeline` shipped in P2 — now a real link.

### Changed

- **Targeted structural refactor (no behavior change)** — split the 74-line
  `prayer.seed_demo()` into `_seed_demo_prayers()` / `_seed_demo_prophecies()`,
  extracted `ws_chat._relay_reply()` to cut `websocket_chat` nesting from 5 to
  3, and completed type annotations across `app.py` page routes and the four
  domain services (`recommend_content`, `class_orchestrator`, `dropout_risk`,
  `realtime._get_client`). *Why:* `anyagent analyze` flagged these as the only
  genuine structural findings; typing/nesting/function-size axes now 100%.

### Investigated / Rejected

- **`anyagent refactor` auto-refactor (63→78 score)** — rejected despite green
  tests: the +15 came from stub docstrings (`"""submit_prayer."""`), collapsing
  formatted fixtures into 2,866-char lines, and deleting load-bearing comments
  (the `llm_client` survival-chain rationale, the `ws_chat` never-echo-provider-
  errors security note). Score gaming, not quality; reverted wholesale. The
  "structure 0%" axis is also deliberately unchased — it rewards class-based
  structure, and the services are intentionally pure module functions.

## [0.8.0] - 2026-06-11

### Added

- **Prayer + prophecy UI at `/me/prayer`** — the ledgers (shipped API-only in
  v0.7) now have a seminarian surface: petitions with visibility + structured
  answers + testimony, peer intercession ("Carried together"), prophetic words
  with 2-of-3 weighing queue and fulfillment recording, and a track-record
  header line. New `Prayer` subnav entry. *Why:* the ledgers were the only
  feature with no human door — agents could use them, people couldn't.
- **Director prayer rhythm on `/cohort`** — counts-only aggregate
  (petitions / intercessions / words / weighings) plus the cohort tradition
  policy toggle (`catholic` / `charismatic`) wired to `/api/cohorts/{id}/policy`.
  Student profiles show a counts-only prayer line. *Why:* REC-7 altitude-1 for
  the ledgers without breaching visibility (content never leaves its circle).
- **Demo seed (`KC_DEMO_SEED=1`)** — `prayer.seed_demo()` populates both
  ledgers with an idempotent demo week. Opt-in only, so tests and fresh API
  consumers start empty.
- **Deployment packaging** — `Dockerfile` (verified locally: build + run +
  smoke), `docker-compose.yml`, `render.yaml`, `fly.toml`, `docs/DEPLOY.md`,
  and a `standalone` extra (ships `fakeredis` for Redis-less hosts). *Why:*
  roadmap "Next" item "Hosted demo deployment".
- **Agent journey skills** (`skills/`) — `morning-check-in`, `cohort-triage`,
  `prayer-ledger`: harness-neutral playbooks over the 20 MCP tools that give
  Claude Code / Codex / Hermes the webapp's role-shaped UX (named statuses,
  plain-English reasons, visibility guardrails). Hermes wiring documented in
  `docs/AGENTS.md`. *Why:* tools ≠ experience; agents should feel like another
  door into the same room.

- **NVIDIA NIM as a free LLM backend, with a survival chain** —
  `llm_client.resolve_chain()` builds the mentor's backend chain from env:
  NVIDIA NIM (free, `integrate.api.nvidia.com/v1`, default
  `openai/gpt-oss-120b`) → local Ollama (always wired, default `qwen2.5:7b`,
  skipped fast when the daemon is down) → OpenRouter → OpenAI. A tier that
  fails before yielding advances the chain; a mid-stream failure re-raises so
  two providers' text is never spliced. `LLM_MODEL` overrides the primary
  tier's model; `LLM_FAKE_RESPONSE` still short-circuits everything.
  Sampling is constrained (`temperature=0.6`, `max_tokens=400`) — the mentor
  speaks in 2-4 sentences. *Why:* free tiers throttle and die
  mid-conversation; the chat should survive that. Failover verified live
  (bogus NIM key → Ollama answered).

- **1-click install + stand up (`./run.sh`)** — creates the venv (uv or
  python3.11+), installs `.[standalone]`, auto-detects a free LLM backend
  (NVIDIA key from env/`~/.hermes/.env` → local Ollama → scripted fallback),
  seeds the demo ledgers, and serves on `:8000`. Verified with a from-scratch
  install. *Why:* the quickstart was five commands and assumed an OpenAI key.

### Changed

- **Frontend cohort data now fetched from `/api/students`** —
  `frontend/cohort_data.js` is an API-backed module (top-level await) instead
  of a duplicated copy of `backend/fixtures/cohort.py`; `getProfile()` is
  async over `/api/students/{id}`. *Why:* removes the documented
  dual-source-of-truth drift risk.
- **Mentor chat opens its WebSocket on page load** — the status pill reads
  "connecting… → connected" instead of sitting on "disconnected" until the
  first send. *Why:* REC-3, the thread should feel alive on arrival.
- Header wordmark no longer wraps on phones (nowrap + hidden below 640px).

### Fixed

- E2E fixtures launched uvicorn with a literal `python`, which fails on
  machines exposing only `python3`/venv interpreters — now `sys.executable`.

### Investigated / Rejected

- **Seeding demo ledgers by default in dev** — rejected: route tests share
  process-global state via `TestClient`, and empty-state copy is a designed
  surface; seeding stays opt-in via `KC_DEMO_SEED=1`.
- **Keeping a static fallback roster in `cohort_data.js`** — rejected: a
  fallback copy re-creates the dual-source drift the change exists to remove;
  on fetch failure pages render their designed error/empty states instead.
- **`${VAR:+...}` env interpolation in docker-compose to auto-switch
  demo/real mode** — rejected as too clever: `LLM_FAKE_RESPONSE` takes
  precedence over `OPENAI_API_KEY` in `llm_client.py`, so implicit switching
  silently keeps the fake; the compose file documents the explicit switch.
- **`moonshotai/kimi-k2.6` as the NIM default mentor model** — rejected after
  live A/B against the app's real prompt: it leaks chain-of-thought into
  `delta.content`, so reasoning monologue reached the chat bubble. `z-ai/glm-5.1`
  rejected for ~35s first-token latency; `deepseek-ai/deepseek-v4-flash` timed
  out. `openai/gpt-oss-120b` answered in ~3s, clean and on-register.
