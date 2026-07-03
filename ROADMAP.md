# Kingdom Come Roadmap

## Now

- Public FastAPI app with the role-shaped UI (door, `/me`, mentor chat, prayer ledger, timeline, cohort overview, triage, groups, student profiles).
- Dropout risk, curriculum, orchestration, and outcome endpoints.
- Cohort and student read endpoints under `/api/` — and the frontend consumes them too (single source of truth in `backend/fixtures/cohort.py`).
- MCP server exposing the formation engines and the AI mentor for Claude Code, Codex, Hermes, OpenCode, and any MCP-aware agent harness — plus journey skills (`skills/`) for webapp-parity agent UX.
- Prayer + prophecy ledgers with longitudinal track records (answer rate, confirmation rate, fulfillment rate), the 1 Cor 14:29 2-of-3 weighing rule, a seminarian surface at `/me/prayer`, and a counts-only director rhythm on `/cohort` with the tradition policy toggle.
- Deploy-ready packaging: verified Dockerfile, compose, Render + Fly blueprints (`docs/DEPLOY.md`), demo seed via `KC_DEMO_SEED=1`.
- Hosted demo instance at https://kingdom-come.fly.dev (Fly.io, demo mode, smoke-checked live: doors, API, OpenAPI, mentor WS).
- Browser E2E coverage for every primary surface and both persona journeys, plus an axe-core accessibility gate over all ten surfaces.
- Opt-in prayer/prophecy ledger persistence (`KC_PERSIST=1` — write-through rows, replayed at startup).
- The Formation Year (`/me/year`), the shared 40-day journey, the director's counts-only pulse note, user-controlled mentor memory, first-run tours, live door previews.
- CSV cohort import on `/cohort`; PWA install + bottom nav on phones.
- One-command installs: `uvx --from git+… kingdom-come`, `docker run ghcr.io/wjlgatech/kingdom-come` (image publishes on next main push), deploy buttons.

## Next

- Publish `kingdom-come` to PyPI (workflow is ready; needs one-time Trusted Publisher setup) and verify the GHCR workflow on main.
- Extend persistence to ministry outcomes and vector memory, with real migrations.
- MCP tools for the new surfaces (mentor memory, journey, pulse note, CSV import) — agent parity with the webapp.
- Better risk explainability and configurable thresholds.
- CSV import for reflections (roster import shipped).
- Visual regression checks.

## Later

- Role-based dashboards for mentors, faculty, and administrators.
- Pluggable model adapters for institutional data.
- Longitudinal ministry outcome analytics.
- Localization for global training contexts.
