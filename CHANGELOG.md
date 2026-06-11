# Changelog

All notable changes to Kingdom Come are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
