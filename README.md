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
├── d17/
│   └── d17-schemat-mesa.png
├── src/
│   └── runaway/
│       ├── __init__.py
│       ├── agents.py
│       ├── cli.py
│       ├── config.py
│       ├── model.py
│       ├── scenarios/
│       │   ├── __init__.py
│       │   ├── d17.py
│       │   └── d17-wall-runs.json
│       └── utils/
│           ├── __init__.py
│           └── png_to_wall_runs.py
└── tests/
    ├── cli/
    ├── model/
    ├── scenarios/
    └── utils/
        └── test_png_to_wall_runs.py
```

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
make install-dev
runaway --steps 100 --agents 60 --preset small
```

## Visualization (Mesa Standard Browser UI)

Run the built-in Mesa server and open the shown local URL in a browser:

```bash
runaway --visualize --steps 300 --agents 80 --preset auto --port 8521
```

`mesa[viz]` is installed by default via project dependencies.
If you use an older environment or hit dependency drift, refresh with:

```bash
pip install -U "mesa[viz]>=2.2,<3.0"
```

Grid notes for D17:
- minimum grid size: `160x90`
- expected aspect ratio: approximately `2938:1662`
- for custom grids, pass both `--width` and `--height` together

## PNG -> wall-runs JSON (optional tool)

If your source is a PNG floor plan, install the optional converter:

```bash
pip install -U "runaway[png]"
```

Then generate `wall-runs-rb-v1` JSON:

```bash
runaway-png2runs --input d17/d17-schemat-mesa.png --output src/runaway/scenarios/d17-wall-runs.json --pretty
```

Note:
- `src/runaway/scenarios/d17-wall-runs.json` is the runtime source used by `build_d17()`.
- `d17/` is a developer workspace (e.g. to keep the original PNG and regenerated artifacts).


## Authors
- Szymon Szarek
- Kamil Rudny