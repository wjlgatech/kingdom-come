# Kingdom Come for Agents

Kingdom Come ships an MCP server (`mcp_server.server`) that exposes the
formation engines, the cohort data, and the AI mentor chat as tools any
MCP-aware agent can call. One server, every framework.

## What agents can do

| Tool | What it does |
|------|--------------|
| `dropout_risk` | Score a student's risk from `engagement` + `reflection_count`; returns level + reasons. |
| `curriculum_recommend` | Recommend curriculum content for a `calling`. |
| `orchestration_plan` | Suggest merge/split actions for small groups. |
| `log_outcome` | Record a ministry outcome and get back an effectiveness band. |
| `list_students` | List the cohort roster (optionally filtered by `cohort_id`). |
| `get_student` | Read a single student profile (reflections, outcomes, risk history). |
| `get_cohort` | Get cohort metadata and director. |
| `list_cohort_outcomes` | List all outcomes for a cohort, newest first. |
| `chat_with_mentor` | Send one message to the mentor pipeline; returns recalled memory + full reply. |

## Setup

Start the FastAPI app first — the MCP server is a thin client over the
HTTP/WS surface:

```bash
python -m pip install -e ".[mcp]"
uvicorn backend.app:app --reload   # leave this running
```

Configuration (env vars, all optional):

| Var | Default | Purpose |
|-----|---------|---------|
| `KC_BASE_URL` | `http://127.0.0.1:8000` | HTTP base for `/api` and form endpoints. |
| `KC_WS_URL` | derived from `KC_BASE_URL` | Override for the WebSocket base (e.g. behind a TLS proxy). |
| `KC_TIMEOUT_S` | `30` | Per-request timeout in seconds. |

For a fully offline demo (no OpenAI / no Redis) set:

```bash
export EMBEDDING_FAKE=1
export LLM_FAKE_RESPONSE="Walk gently into this week."
```

## Wiring it up

### Claude Code

The plugin manifest at `.claude-plugin/plugin.json` declares the MCP server.
From the repo root:

```bash
claude mcp add-from-plugin .   # or the equivalent UI add-plugin step
```

Or, if you prefer raw MCP config, add this to `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "kingdom-come": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "env": { "KC_BASE_URL": "http://127.0.0.1:8000" }
    }
  }
}
```

### Codex CLI

Codex reads MCP servers from `~/.codex/config.toml`:

```toml
[mcp_servers.kingdom-come]
command = "python"
args = ["-m", "mcp_server.server"]
env = { KC_BASE_URL = "http://127.0.0.1:8000" }
```

### OpenCode / other MCP-aware harnesses

Any framework that speaks MCP over stdio can launch the same command:

```
python -m mcp_server.server
```

Pass `KC_BASE_URL` (and optionally `KC_WS_URL`, `KC_TIMEOUT_S`) via the
harness's environment-variable hook. If a framework doesn't support MCP,
agents can call the FastAPI directly — `/predictive/dropout-risk`,
`/curriculum/recommendations`, `/orchestration/actions`, `/outcomes`,
`/api/students`, `/api/students/{id}`, `/api/cohorts/{id}`,
`/api/cohorts/{id}/outcomes` — and the WS at `/ws/chat`.

### Run the server standalone (debugging)

```bash
python -m mcp_server.server   # speaks MCP over stdio; pipe MCP framing in/out
```

## Examples

A director-side agent (read-only triage):

```
agent: list_students()
agent: dropout_risk(engagement=0.18, reflection_count=0)
agent: get_student("stu-sarah-k")          # see her recent reflections + risk arc
agent: list_cohort_outcomes("st-aloysius-s26")
```

A seminarian-side agent (reflection + mentor):

```
agent: chat_with_mentor("stu-marcus-r", "I'm wrestling with the readings this week.")
agent: curriculum_recommend(calling="evangelism", completed_content=["mission_theology"])
```

A formation director logging a field outcome:

```
agent: log_outcome("stu-anna-t", 0.86, "Led a supervised neighborhood cohort.")
```

## Notes

- The cohort/student endpoints under `/api/...` are namespaced so they don't
  collide with the Jinja page routes (`/students/{id}` is the director-facing
  HTML profile; `/api/students/{id}` is the JSON for agents).
- `chat_with_mentor` collapses the streaming WebSocket into a single
  response. If the surrounding harness needs token-by-token streaming, call
  `/ws/chat` directly — the contract is `memory → chunks → done`.
- The fixtures live in `backend/fixtures/cohort.py` (ported from
  `frontend/cohort_data.js`). Replace with real persistence when the
  product crosses that line.
