.PHONY: lint lint-fix format format-check typecheck semgrep security test check install-hooks

lint:
	ruff check src migrations tests

lint-fix:
	ruff check --fix src migrations tests

format:
	ruff format src migrations tests

format-check:
	ruff format --check src migrations tests

typecheck:
	pyright

semgrep:
	pre-commit run semgrep --all-files

security:
	bandit -r src migrations --baseline .bandit-baseline.json
	$(MAKE) semgrep

test:
	pytest

check: lint format-check typecheck security test

install-hooks:
	python -m pre_commit install
