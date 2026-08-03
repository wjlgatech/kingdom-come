# Kingdom Come — one command to a running, seeded app.
#
#   make demo     install (first run) + serve + open the browser   ← start here
#   make install  dev extras + Playwright chromium
#   make test     full suite (unit + API + WS + E2E + a11y)
#   make check    the ship gate: compile + full suite
#
# The public demo needs nothing installed at all: https://kingdom-come.fly.dev

.DEFAULT_GOAL := demo
.PHONY: demo serve install test check fast-test brand-verify clean

PY := .venv/bin/python
PORT ?= 8000

demo:
	@./run.sh

# Same app, no browser — for containers, CI, and remote hosts.
serve: | $(PY)
	$(PY) -m backend.cli --no-open --port $(PORT)

$(PY):
	python3 -m venv .venv
	$(PY) -m pip install --quiet --upgrade pip

install: | $(PY)
	$(PY) -m pip install -e ".[dev]"
	$(PY) -m playwright install chromium

test: | $(PY)
	$(PY) -m pytest

# Skip the slow Playwright suites while iterating on the backend.
fast-test: | $(PY)
	$(PY) -m pytest --ignore=tests/test_e2e.py --ignore=tests/test_e2e_kc.py

check: | $(PY)
	$(PY) -m compileall -q backend tests
	$(PY) -m pytest

# Assert the LIVE deploy serves the brand this repo ships (catches deploy drift).
brand-verify: | $(PY)
	KC_CHECK_LIVE=1 $(PY) -m pytest tests/test_demo_entry.py -v

clean:
	rm -rf .pytest_cache **/__pycache__ formation.db
