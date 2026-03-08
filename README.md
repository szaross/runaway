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
│           └── d17.py
└── tests/
	└── test_fake.py
```

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
make install-dev
runaway --steps 100 --agents 60 --width 25 --height 18
```

## Authors
- Szymon Szarek
- Kamil Rudny