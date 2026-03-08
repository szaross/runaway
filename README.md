# Runaway

Agent-based evacuation simulation for building layouts using the Mesa library.

## Project Goals

- Model evacuee behavior in constrained indoor spaces.
- Simulate bottlenecks at exits and corridors.
- Measure evacuation performance over time.

## Project Structure

```text
.
├── pyproject.toml
├── src/
│   └── runaway/
│       ├── __init__.py
│       ├── agents.py
│       ├── cli.py
│       ├── config.py
│       ├── model.py
│       └── scenarios/
│           ├── __init__.py
│           └── simple_floor.py
└── tests/
	└── test_model.py
```

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
runaway --steps 100 --agents 60 --width 25 --height 18
```

## Run Tests

```bash
pytest
```

## Code Formatting

Format all Python files:

```bash
ruff format .
```

Run lint checks (including import order):

```bash
ruff check .
```

Auto-fix lint issues when possible:

```bash
ruff check . --fix
```