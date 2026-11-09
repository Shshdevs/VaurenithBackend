.PHONY: lint lint-fix format format-check typecheck semgrep semgrep-all security test test-unit test-integration test-cov check fix setup install-hooks docker docker-up docker-build docker-down docker-logs db-upgrade db-upgrade-test db-current db-revision

PYTHON ?= python3.13
TEST_PATH ?= tests
PYTEST_ARGS ?=
MESSAGE ?=

lint:
	ruff check src migrations tests

lint-fix:
	ruff check --fix src migrations tests

format:
	ruff format src migrations tests

format-check:
	ruff format --check src migrations tests

fix:
	$(MAKE) lint-fix
	$(MAKE) format

typecheck:
	pyright

semgrep:
	pre-commit run semgrep

semgrep-all:
	pre-commit run semgrep --all-files

security:
	bandit -r src migrations --baseline .bandit-baseline.json
	$(MAKE) semgrep-all

test:
	pytest $(TEST_PATH) $(PYTEST_ARGS)

test-unit:
	pytest tests/unit $(PYTEST_ARGS)

test-integration:
	@$(PYTHON) -c 'from dotenv import dotenv_values; import os, sys; sys.exit(0 if os.getenv("TEST_DATABASE_URL") or dotenv_values(".env").get("TEST_DATABASE_URL") else "Set TEST_DATABASE_URL in the environment or .env before running integration tests.")'
	pytest tests/integration $(PYTEST_ARGS)

test-cov:
	pytest $(TEST_PATH) $(PYTEST_ARGS) --cov=app --cov-report=term-missing

check: lint format-check typecheck security test

setup:
	$(PYTHON) -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements-dev.txt
	@if [ ! -f .env ]; then cp .env.example .env; fi
	.venv/bin/pre-commit install
	.venv/bin/pre-commit install --hook-type commit-msg

install-hooks:
	pre-commit install
	pre-commit install --hook-type commit-msg

docker: docker-up

docker-up:
	docker compose up --build

docker-build:
	docker compose build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

db-upgrade:
	alembic upgrade head

db-upgrade-test:
	python scripts/migrate_test_database.py

db-current:
	alembic current

db-revision:
	@test -n "$(MESSAGE)" || { echo "Usage: make db-revision MESSAGE='describe migration'" >&2; exit 1; }
	alembic revision --autogenerate -m "$(MESSAGE)"
