.PHONY: help install install-dev test lint format format-check check c clean

help:
	@echo "Available commands:"
	@echo "  make install       Install the package"
	@echo "  make install-dev   Install package with dev dependencies"
	@echo "  make test          Run pytest"
	@echo "  make lint          Check code style with ruff"
	@echo "  make format        Format code with ruff"
	@echo "  make format-check  Check formatting without modifying files"
	@echo "  make check (c)     Run lint, format check, and test (pre-commit checks)"
	@echo "  make clean         Remove build artifacts and cache"

install:
	pip install -e .

install-dev:
	pip install -e .[dev]

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

format-check:
	ruff format --check .

check: lint format-check test

c: check

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache/ .ruff_cache/ **/__pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

