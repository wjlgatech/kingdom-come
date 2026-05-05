# Contributing To Kingdom Come

Thanks for helping make formation software better.

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m playwright install chromium
python -m pytest
uvicorn backend.app:app --reload
```

## Development Standards

- Keep changes small and focused.
- Add or update tests for behavior changes.
- Run `python -m pytest` before opening a PR.
- Prefer clear domain language over clever abstractions.
- Explain formation-impact assumptions in issues or PR descriptions.

## Pull Requests

Every PR should include:

- What changed.
- Why it matters.
- How it was tested.
- Any screenshots for UI changes.

## Good First Issues

- Add more service fixtures.
- Improve error messages.
- Add persistent outcome storage.
- Add deployment docs.
- Improve keyboard and screen reader support.
