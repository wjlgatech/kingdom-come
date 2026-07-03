# Kingdom Come

**Predictive formation intelligence for teams shaping resilient ministry leaders.**

Kingdom Come is an open-source FastAPI platform for seminaries, church networks, and ministry training teams that want to move from scattered spreadsheets to real formation signals. It combines dropout risk detection, adaptive curriculum recommendations, live class orchestration, and ministry outcome tracking in one contributor-friendly project.

**[Try the live demo →](https://kingdom-come.fly.dev)** (seeded demo week, scripted mentor — nothing to install)

[Explore the repo](https://github.com/wjlgatech/kingdom-come) · [Run locally](#quickstart) · [Contribute](#contribute)

## Start here

These four docs are the project's home base. Read them in order if you're new.

| Doc | What it answers | Who it's for |
|-----|-----------------|--------------|
| [What it is](docs/WHAT-IT-IS.md) | What problem does Kingdom Come solve and why does it matter? | Anyone — written so a 15-year-old can follow it. |
| [How to use it](docs/HOW-TO-USE.md) | What you'll see and do in the app, screen by screen. | Students and teachers — no jargon. |
| [How it works](docs/ARCHITECTURE.md) | The runtime, services, and design principles under the hood. | Contributors and engineers. |
| [Prayer + prophecy](docs/PRAYER.md) | The two track-record ledgers and the 2-of-3 weighing rule. | Contributors and formation directors. |
| [Roadmap](ROADMAP.md) | What's shipping now, what's next, what's later. | Anyone tracking the project's direction. |

## Why This Exists

Formation teams often see warning signs late: disengagement, thin reflection habits, overloaded cohorts, and ministry outcomes that never make it back into curriculum design. Kingdom Come makes those signals visible early, explainable, and testable.

What you get on day one:

- **Predictive risk signals** for engagement and reflection patterns.
- **Adaptive curriculum paths** based on calling and completed content.
- **Class orchestration actions** that identify groups needing intervention.
- **Ministry outcome snapshots** that connect field impact back to formation.
- **An AI mentor with memory you control** — view and forget what it remembers.
- **Prayer + prophecy ledgers** with track records that can persist across restarts (`KC_PERSIST=1`).
- **The Formation Year** (`/me/year`) — a student's whole year assembled as one editorial page.
- **CSV roster import**, a shared 40-day journey, installable PWA, first-run tours.
- **A real web workbench** backed by the same JSON API your integrations can call.
- **Unit, API, browser E2E, and axe-core accessibility tests** so contributors can move with confidence.

## Product Preview

Run the app and open `http://127.0.0.1:8000` to use the formation workbench:

- Assess dropout risk with common and invalid edge-case inputs.
- Generate curriculum recommendations for a student calling.
- Plan class orchestration from group rosters.
- Track ministry outcomes and effectiveness snapshots.

The OpenAPI docs are available at `http://127.0.0.1:8000/docs`.

## Quickstart

One command — installs on first run, picks a free LLM backend automatically
(NVIDIA NIM key if found → local Ollama → scripted fallback), seeds the demo,
and serves at `http://127.0.0.1:8000`:

```bash
./run.sh
```

For development (tests, Playwright):

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m playwright install chromium
python -m pytest
uvicorn backend.app:app --reload
```

## API Examples

```bash
curl -s http://127.0.0.1:8000/health

curl -s -X POST http://127.0.0.1:8000/predictive/dropout-risk \
  -H "Content-Type: application/json" \
  -d '{"engagement":0.18,"reflection_count":1}'

curl -s -X POST http://127.0.0.1:8000/curriculum/recommendations \
  -H "Content-Type: application/json" \
  -d '{"calling":"evangelism","completed_content":[]}'

curl -s -X POST http://127.0.0.1:8000/orchestration/actions \
  -H "Content-Type: application/json" \
  -d '[{"id":"alpha","members":["Ana","Bo"]}]'

curl -s -X POST http://127.0.0.1:8000/outcomes \
  -H "Content-Type: application/json" \
  -d '{"student_id":"stu-7","impact_score":0.86,"description":"Led a supervised neighborhood cohort."}'

curl -s http://127.0.0.1:8000/api/students | jq '.students | length'
curl -s http://127.0.0.1:8000/api/cohorts/st-aloysius-s26/outcomes

# Prayer + prophecy track records (see docs/PRAYER.md)
curl -s -X POST http://127.0.0.1:8000/api/prayer/requests \
  -H "Content-Type: application/json" \
  -d '{"student_id":"stu-marcus-r","petition":"Wisdom for the Mission Theology essay.","recipient_ids":["stu-luca-b","stu-grace-w"]}'
curl -s http://127.0.0.1:8000/api/prayer/track-record/stu-marcus-r
curl -s http://127.0.0.1:8000/api/cohorts/st-aloysius-s26/prayer-rhythm
```

## Prayer + prophecy track records

Two parallel ledgers with longitudinal track records — was this prayer
answered? was this prophecy confirmed by 2-of-3 weighers? was it ultimately
fulfilled? Read [`docs/PRAYER.md`](docs/PRAYER.md) for the full data model,
the 1 Cor 14:29 weighing rule, and the visibility / track-record stats.

In the app: seminarians work the ledgers at `/me/prayer` (petitions,
intercession, weighing queue, fulfillment); directors see a counts-only
prayer rhythm on `/cohort` plus the cohort tradition policy toggle.
Set `KC_DEMO_SEED=1` to start with a lived-in demo week.

## Deploy it

A hosted demo runs at **https://kingdom-come.fly.dev** (Fly.io, demo mode,
scales to zero when idle).

One command, no clone (needs [uv](https://docs.astral.sh/uv/)):

```bash
uvx --from git+https://github.com/wjlgatech/kingdom-come kingdom-come
```

One click — get your own hosted instance (demo mode, zero secrets needed):

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/wjlgatech/kingdom-come)

Or one command on Fly.io:

```bash
fly launch --copy-config --now   # uses the shipped fly.toml
```

The repo is deploy-ready: a verified `Dockerfile`, `docker-compose.yml`
(demo mode out of the box), and blueprints for Render (`render.yaml`) and
Fly.io (`fly.toml`). See [`docs/DEPLOY.md`](docs/DEPLOY.md).

```bash
docker compose up --build   # → http://127.0.0.1:8000, seeded demo
```

## For agents (Claude Code, Codex, OpenCode, …)

Kingdom Come ships an MCP server that wraps the API as 20 tools — formation
scoring, curriculum recommendations, class orchestration, outcome logging,
cohort/student reads, the AI mentor chat, and the prayer + prophecy ledgers
(submit, weigh, mark answered, record fulfillment, pull track records). Any
MCP-aware harness can use it.

```bash
python -m pip install -e ".[mcp]"
uvicorn backend.app:app --reload      # KC API on :8000
python -m mcp_server.server           # MCP server over stdio
```

Wiring snippets for Claude Code, Codex, Hermes, and other harnesses are in
[`docs/AGENTS.md`](docs/AGENTS.md). A Claude Code plugin manifest at
[`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) registers the
server automatically, and three journey skills in [`skills/`](skills) —
`morning-check-in`, `cohort-triage`, `prayer-ledger` — give agents the same
role-shaped experience the webapp gives Marcus and Sister Theresa.

## Project Structure

```text
backend/        FastAPI app, database wiring, models, domain services
frontend/      Static product UI served by FastAPI
mcp_server/    MCP server wrapping the API for agent harnesses
skills/        Agent journey skills (webapp-parity playbooks over MCP)
.claude-plugin/ Claude Code plugin manifest
tests/         Unit, API, static UI, and browser E2E tests
docs/          Feature notes, architecture, deployment, and plans
```

## Test Matrix

```bash
python -m compileall backend tests
python -m pytest
```

Coverage includes service logic, API contracts, static asset serving, and a real Chromium E2E flow through the four core workbench workflows.

## Configuration

The mentor chat runs on a **fallback chain** so it survives free-tier
throttles and outages. Tiers are tried in order; a tier joins the chain when
its env var is present:

| Tier | Env var | Default model |
|------|---------|---------------|
| 0. Scripted fake (tests/offline) | `LLM_FAKE_RESPONSE` — beats everything | — |
| 1. NVIDIA NIM (**free**, build.nvidia.com, ~40 req/min) | `NVIDIA_API_KEY` | `openai/gpt-oss-120b` |
| 2. Local Ollama (always wired; skipped when not running) | `OLLAMA_MODEL` / `OLLAMA_BASE_URL` optional | `qwen2.5:7b` |
| 3. OpenRouter | `OPENROUTER_API_KEY` | `openai/gpt-5-mini` |
| 4. OpenAI | `OPENAI_API_KEY` | `gpt-4o-mini` |

`LLM_MODEL` overrides the primary tier's model. Without an OpenAI key,
embeddings use a deterministic fake — fine for demos.

The database defaults to `sqlite:///./formation.db`. Override it with:

```bash
export DATABASE_URL="sqlite:///./formation.db"
```

## Contribute

Kingdom Come is public because formation software should be shaped by educators, technologists, ministry practitioners, data scientists, designers, and students together.

Good first contributions:

- Improve formation risk scoring with better explainability.
- Add accessibility audits and UI refinements.
- Add deployment guides for Render, Fly.io, Railway, or Docker.
- Expand ministry outcome models and persistence.
- Add fixtures that reflect real cohort scenarios.

Start with [CONTRIBUTING.md](CONTRIBUTING.md), scan [ROADMAP.md](ROADMAP.md), and open an issue before large changes.

## License

MIT. Build with it, teach with it, improve it, and send the useful parts back.
