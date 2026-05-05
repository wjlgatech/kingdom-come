# Seminary Formation Platform V7

## Overview
FastAPI backend for:

- Predictive dropout detection
- Adaptive curriculum recommendations
- Ministry outcome tracking model support
- Real-time class orchestration actions

## Requirements

- Python 3.11+

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Run

```bash
uvicorn backend.app:app --reload
```

Then open:

- API health: `http://127.0.0.1:8000/health`
- OpenAPI docs: `http://127.0.0.1:8000/docs`

## Test

```bash
python -m pytest
```

## Configuration

The database defaults to `sqlite:///./formation.db`. Override it with:

```bash
export DATABASE_URL="sqlite:///./formation.db"
```
