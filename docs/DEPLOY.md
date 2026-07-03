# Deploying Kingdom Come

The app is a single FastAPI process serving the UI, the JSON API, and the
WebSocket mentor chat. One container, no build chain, no external services
required — Redis, the database, and the LLM all have graceful fallbacks.

> **⚠️ Demo / pilot posture — not yet production.** The app has **no
> authentication and no rate limiting** (see `PLAN-REDESIGN.md` → "NOT in
> scope"). Anyone who can reach it can read every cohort-visible prayer,
> submit petitions/words as any student id, and use `/ws/chat` as an open LLM
> relay against whatever key you attach. The shipped configs bind Docker to
> `127.0.0.1` and ship demo data. Before any public, multi-user, or
> real-data deployment: put it behind an authenticating reverse proxy (or
> your platform's access control), and do **not** attach a high-limit
> `OPENAI_API_KEY` to a publicly reachable instance. A free `NVIDIA_API_KEY`
> (40 req/min) is the safer key to expose for a demo.

## Modes

| Mode | What it does | Env vars |
|------|--------------|----------|
| **Demo** (default in all shipped configs) | Seeded prayer/prophecy ledgers, deterministic fake embeddings, scripted mentor reply. Works with zero secrets. | `KC_DEMO_SEED=1`, `LLM_FAKE_RESPONSE="..."` |
| **Real, free** | Streaming mentor via NVIDIA NIM (default `openai/gpt-oss-120b`, ~40 req/min dev tier — fine for a cohort). | `NVIDIA_API_KEY=nvapi-...` and **remove** `LLM_FAKE_RESPONSE` (the fake takes precedence in `llm_client.py`) |
| **Real, OpenAI** | OpenAI embeddings + streaming `gpt-4o-mini` mentor. | `OPENAI_API_KEY=sk-...` and **remove** `LLM_FAKE_RESPONSE`. |

The chat backend is a fallback chain (NIM → local Ollama → OpenRouter →
OpenAI; see README "Configuration") — set any subset of
`NVIDIA_API_KEY` / `OPENROUTER_API_KEY` / `OPENAI_API_KEY` as platform
secrets and the chain assembles itself. On hosted platforms the Ollama tier
simply skips (no local daemon).

Other knobs:

| Var | Default | Purpose |
|-----|---------|---------|
| `PORT` | `8000` | Listen port (container CMD honors it). |
| `REDIS_URL` | unset → in-process `fakeredis` | Real Redis for activity events. |
| `DATABASE_URL` | `sqlite:///./formation.db` | SQLAlchemy URL (tables are opt-in via `init_db()`). |
| `KC_DEMO_SEED` | unset | `1` seeds the prayer + prophecy ledgers with a demo week (idempotent, in-memory). |
| `KC_PERSIST` | unset | `1` persists the prayer + prophecy ledgers to `DATABASE_URL` (write-through rows, replayed at startup). Run exactly one machine, and give sqlite a volume — a redeploy replaces the container filesystem. |
| `KC_JOURNEY_START` | 11 days ago | ISO date the shared 40-day journey began (drives the "Day N of 40" lines). |
| `EMBEDDING_FAKE` | unset | `1` forces fake embeddings even when a key is present. |
| `LLM_MODEL` | per provider | Override the chat model id (NVIDIA default `openai/gpt-oss-120b`, OpenAI default `gpt-4o-mini`). |

> **State note:** vector memory and activity events are in-process by design
> (see `docs/ARCHITECTURE.md`) and reset on redeploy. The prayer + prophecy
> ledgers reset too **unless** you set `KC_PERSIST=1` (write-through rows in
> `DATABASE_URL`, replayed at startup) — with sqlite, mount a volume so the
> DB outlives the container.

## Docker (verified locally)

A prebuilt image publishes to GHCR on every push to `main`
(`.github/workflows/publish-image.yml`):

```bash
docker run -p 8000:8000 ghcr.io/wjlgatech/kingdom-come   # no clone needed
```

Or build it yourself:

```bash
docker build -t kingdom-come .
docker run -p 8000:8000 -e KC_DEMO_SEED=1 \
  -e LLM_FAKE_RESPONSE="Walk gently into this week." kingdom-come
# → http://127.0.0.1:8000
```

Or with compose (demo mode out of the box):

```bash
docker compose up --build
```

## Render

One click:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/wjlgatech/kingdom-come)

Or from the dashboard — the repo ships a [`render.yaml`](../render.yaml) blueprint:

1. Push the repo to GitHub (or use the button above on the public repo).
2. Render dashboard → **New → Blueprint** → pick the repo.
3. Deploy. The free plan works; `/health` is the health check.
4. Real mentor: set `OPENAI_API_KEY` in the dashboard and delete the
   `LLM_FAKE_RESPONSE` env var.

## Fly.io

The reference demo instance runs here: **https://kingdom-come.fly.dev**
(demo mode, `auto_stop_machines` — first request after idle takes a few
seconds while a machine wakes).

The repo ships a [`fly.toml`](../fly.toml):

```bash
fly launch --copy-config --no-deploy   # creates the app, keeps our config
fly deploy --ha=false                  # ONE machine — see note below
fly secrets set OPENAI_API_KEY=sk-...  # optional, for the real mentor
```

> **Run exactly one machine** (`--ha=false`, or `fly scale count 1` after the
> fact). The ledgers, vector memory, and events are in-process; two machines
> means two divergent states behind one hostname — a prayer marked answered
> on one machine still shows open when the next request lands on the other.

## Railway / anything that runs a Dockerfile

Point the platform at the repo root; it will pick up the `Dockerfile`.
Set the env vars from the table above. Health check: `GET /health`.

## After deploying

Smoke checklist (the same flows the E2E suite covers):

1. `/` shows the two role doors.
2. Seminarian door → `/me` → `Begin reflection` → the mentor streams a reply.
3. `/me/prayer` shows the seeded ledger (demo mode) and `+ New petition` works.
4. Director door → `/cohort` shows the engagement chart + prayer rhythm.
5. `/cohort/triage` → click a student → `+ Log outcome` round-trips.
6. `https://<host>/docs` serves the OpenAPI explorer.

To point the MCP server at a hosted instance:

```bash
KC_BASE_URL=https://<your-host> python -m mcp_server.server
```
