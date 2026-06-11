#!/usr/bin/env bash
# Kingdom Come — 1-click install + stand up.
#
#   ./run.sh                 install (first run only) + start on :8000
#   PORT=9000 ./run.sh       different port
#   KC_DEMO_SEED=0 ./run.sh  start with empty ledgers
#
# LLM backend defaults to the free survival chain (free-llm):
#   NVIDIA NIM (NVIDIA_API_KEY, free at build.nvidia.com) → local Ollama →
#   OpenRouter → OpenAI. With no backend at all, the mentor falls back to a
#   scripted reply so every surface still works.
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-8000}"
VENV=".venv"
PY="$VENV/bin/python"

say() { printf '\033[1m%s\033[0m\n' "$*"; }

# ---- 1. Python env (uv if available, else python3.12/3.11) ----------------
if [ ! -x "$PY" ]; then
  say "Setting up Python environment…"
  if command -v uv >/dev/null 2>&1; then
    uv venv "$VENV" --python 3.11
  else
    PYBIN="$(command -v python3.12 || command -v python3.11 || true)"
    if [ -z "$PYBIN" ]; then
      echo "Need Python ≥3.11. Install uv (https://docs.astral.sh/uv/) or python3.11+." >&2
      exit 1
    fi
    "$PYBIN" -m venv "$VENV"
  fi
fi

# ---- 2. Install deps (skipped when already importable) --------------------
if ! "$PY" -c "import fastapi, faiss, fakeredis" >/dev/null 2>&1; then
  say "Installing Kingdom Come (one-time)…"
  if command -v uv >/dev/null 2>&1; then
    uv pip install -p "$PY" -e ".[standalone]" --quiet
  else
    "$PY" -m pip install --quiet -e ".[standalone]"
  fi
fi

# ---- 3. Free-LLM defaults (free-llm survival chain) ------------------------
# If no LLM key is already exported, try to pick up a free NVIDIA NIM key from
# a local .env (repo-local first, then ~/.hermes/.env). We announce which file
# we read so key provenance is never silent. Strip surrounding quotes and any
# trailing inline comment so a quoted/annotated value can't produce a 401.
NIM_SRC=""
if [ -z "${NVIDIA_API_KEY:-}" ]; then
  for f in ".env" "$HOME/.config/nvidia/nim.env" "$HOME/.hermes/.env"; do
    [ -f "$f" ] || continue
    k="$(grep -h '^NVIDIA_API_KEY=' "$f" 2>/dev/null | head -1 | cut -d= -f2-)" || true
    k="${k%%#*}"                     # drop inline comment
    k="$(printf '%s' "$k" | tr -d '"'\''[:space:]')"  # drop quotes/whitespace
    if [ -n "${k:-}" ]; then export NVIDIA_API_KEY="$k"; NIM_SRC="$f"; break; fi
  done
fi

# Pick the backend banner. The chain itself (llm_client.py) tries NIM → Ollama
# → OpenRouter → OpenAI; only force the scripted fallback when NO real backend
# key is present AND no local Ollama is up, so a user's paid key is never
# silently overridden.
if [ -n "${NVIDIA_API_KEY:-}" ]; then
  BACKEND="NVIDIA NIM (free)${NIM_SRC:+, key from $NIM_SRC} with Ollama/OpenRouter/OpenAI failover"
elif [ -n "${OPENROUTER_API_KEY:-}" ] || [ -n "${OPENAI_API_KEY:-}" ]; then
  BACKEND="configured key (OpenRouter/OpenAI) with failover"
elif curl -s --max-time 1 "http://localhost:11434/api/tags" >/dev/null 2>&1; then
  BACKEND="local Ollama"
else
  export LLM_FAKE_RESPONSE="${LLM_FAKE_RESPONSE:-Walk gently into this week. What you named is worth one more honest paragraph.}"
  BACKEND="scripted fallback (set NVIDIA_API_KEY for the free real mentor — build.nvidia.com)"
fi

export KC_DEMO_SEED="${KC_DEMO_SEED:-1}"

# ---- 4. Stand up ------------------------------------------------------------
say "Kingdom Come → http://127.0.0.1:$PORT"
say "Mentor backend: $BACKEND"
[ "$KC_DEMO_SEED" = "1" ] && say "Demo ledgers: seeded (KC_DEMO_SEED=0 to disable)"
exec "$PY" -m uvicorn backend.app:app --host 127.0.0.1 --port "$PORT"
