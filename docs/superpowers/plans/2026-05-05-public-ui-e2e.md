# Public UI And E2E Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn Kingdom Come into a public, contributor-ready FastAPI product with a polished UI, E2E browser coverage, and public-facing documentation.

**Architecture:** FastAPI serves both JSON endpoints and a static web app from `frontend/`. The UI uses native HTML/CSS/JavaScript so the project remains easy for contributors to run without a frontend build chain. E2E tests launch the ASGI app with Uvicorn and exercise the real browser workflow through Playwright.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy, static HTML/CSS/JS, pytest, Python Playwright.

---

### Task 1: UI Contract Tests

**Files:**
- Create: `tests/test_ui.py`
- Create: `tests/test_e2e.py`

- [x] Write tests for static landing page serving, dashboard text, and browser workflows.
- [x] Run the tests red before adding UI files.

### Task 2: Static App

**Files:**
- Modify: `backend/app.py`
- Create: `frontend/index.html`
- Create: `frontend/styles.css`
- Create: `frontend/app.js`

- [x] Serve `/` and `/static/*` from FastAPI.
- [x] Build an operational first screen with dropout risk, curriculum, orchestration, and outcome sections.
- [x] Add resilient client-side form handling and error states.

### Task 3: Public Contributor Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/V7_FEATURES.md`
- Create: `CONTRIBUTING.md`
- Create: `ROADMAP.md`
- Create: `.github/ISSUE_TEMPLATE/bug_report.md`
- Create: `.github/ISSUE_TEMPLATE/feature_request.md`
- Create: `.github/pull_request_template.md`

- [x] Rewrite README as a public landing page with quickstart, screenshots guidance, API examples, and contribution CTA.
- [x] Add contributor workflow, roadmap, and GitHub templates.

### Task 4: Verification And Publish

**Files:**
- Modify: committed project files only.

- [x] Run compile, unit/API tests, E2E tests, and browser smoke checks.
- [x] Commit and push to public GitHub repo.
