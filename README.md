# Kingdom Come

**Predictive formation intelligence for teams shaping resilient ministry leaders.**

Kingdom Come is an open-source FastAPI platform for seminaries, church networks, and ministry training teams that want to move from scattered spreadsheets to real formation signals. It combines dropout risk detection, adaptive curriculum recommendations, live class orchestration, and ministry outcome tracking in one contributor-friendly project.

[Explore the repo](https://github.com/wjlgatech/kingdom-come) · [Run locally](#quickstart) · [Contribute](#contribute)

## Why This Exists

Formation teams often see warning signs late: disengagement, thin reflection habits, overloaded cohorts, and ministry outcomes that never make it back into curriculum design. Kingdom Come makes those signals visible early, explainable, and testable.

What you get on day one:

- **Predictive risk signals** for engagement and reflection patterns.
- **Adaptive curriculum paths** based on calling and completed content.
- **Class orchestration actions** that identify groups needing intervention.
- **Ministry outcome snapshots** that connect field impact back to formation.
- **A real web workbench** backed by the same JSON API your integrations can call.
- **Unit, API, and browser E2E tests** so contributors can move with confidence.

## Product Preview

Run the app and open `http://127.0.0.1:8000` to use the formation workbench:

- Assess dropout risk with common and invalid edge-case inputs.
- Generate curriculum recommendations for a student calling.
- Plan class orchestration from group rosters.
- Track ministry outcomes and effectiveness snapshots.

The OpenAPI docs are available at `http://127.0.0.1:8000/docs`.

## Quickstart

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
```

## Project Structure

```text
backend/       FastAPI app, database wiring, models, domain services
frontend/      Static product UI served by FastAPI
tests/         Unit, API, static UI, and browser E2E tests
docs/          Feature notes, architecture, and implementation plans
```

## Test Matrix

```bash
python -m compileall backend tests
python -m pytest
```

Coverage includes service logic, API contracts, static asset serving, and a real Chromium E2E flow through the four core workbench workflows.

## Configuration

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
