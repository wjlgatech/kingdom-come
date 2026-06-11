# Kingdom Come Roadmap

## Now

- Public FastAPI app with the role-shaped UI (door, `/me`, mentor chat, prayer ledger, timeline, cohort overview, triage, groups, student profiles).
- Dropout risk, curriculum, orchestration, and outcome endpoints.
- Cohort and student read endpoints under `/api/` — and the frontend consumes them too (single source of truth in `backend/fixtures/cohort.py`).
- MCP server exposing the formation engines and the AI mentor for Claude Code, Codex, Hermes, OpenCode, and any MCP-aware agent harness — plus journey skills (`skills/`) for webapp-parity agent UX.
- Prayer + prophecy ledgers with longitudinal track records (answer rate, confirmation rate, fulfillment rate), the 1 Cor 14:29 2-of-3 weighing rule, a seminarian surface at `/me/prayer`, and a counts-only director rhythm on `/cohort` with the tradition policy toggle.
- Deploy-ready packaging: verified Dockerfile, compose, Render + Fly blueprints (`docs/DEPLOY.md`), demo seed via `KC_DEMO_SEED=1`.
- Browser E2E coverage for every primary surface and both persona journeys.

## Next

- Hosted demo instance (configs are ready; needs a platform account to point them at).
- Persistent prayer/outcome records with migrations (the in-process ledgers reset on redeploy).
- Better risk explainability and configurable thresholds.
- CSV import for cohorts and reflections.
- Accessibility report and visual regression checks.

## Later

- Role-based dashboards for mentors, faculty, and administrators.
- Pluggable model adapters for institutional data.
- Longitudinal ministry outcome analytics.
- Localization for global training contexts.
