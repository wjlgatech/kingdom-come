# Kingdom Come — production image.
# Serves the web app + JSON API on $PORT (default 8000).
#
# Demo mode (no OpenAI key, seeded ledgers):
#   docker run -p 8000:8000 -e KC_DEMO_SEED=1 -e EMBEDDING_FAKE=1 \
#     -e LLM_FAKE_RESPONSE="Walk gently into this week." kingdom-come
# Real mode:
#   docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... kingdom-come
FROM python:3.11-slim

# faiss-cpu wheels need libgomp at runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

COPY pyproject.toml README.md LICENSE ./
COPY backend ./backend
COPY mcp_server ./mcp_server
COPY frontend ./frontend

RUN pip install --no-cache-dir ".[standalone]"

# Drop root — an app-level RCE shouldn't own the container.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
CMD ["sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
