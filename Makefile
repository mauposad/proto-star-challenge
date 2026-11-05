.PHONY: setup lint format typecheck test check train predict clean

setup:  ## Create .venv, install deps, install git hooks
	uv sync
	uv run pre-commit install

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy

test:
	uv run pytest --cov=proto_star --cov-report=term-missing

check: lint typecheck test  ## Everything CI runs

CONFIG ?= configs/baseline.yaml
train:
	uv run proto-star train $(CONFIG)

RUN ?=
predict:
	uv run proto-star predict $(RUN)

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov
