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
│       ├── core/
│       │   ├── agents.py
│       │   ├── config.py
│       │   ├── floors.py
│       │   └── model.py
│       ├── cli/
│       │   ├── grid_presets.py
│       │   └── main.py
│       ├── renderers/
│       │   ├── base.py
│       │   ├── mesa.py
│       │   └── pygame.py
│       ├── experiments/
│       │   ├── batch.py
│       │   ├── plan.py
│       │   └── results.py
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
    ├── utils/
    └── visualization/
```

Note:
- root-level modules like `runaway.model` and `runaway.cli` are kept as compatibility shims,
- new development should target subpackages (`runaway.core`, `runaway.renderers`, `runaway.cli.main`, `runaway.experiments`).

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

Multifloor example (identical floor layouts + default stairs links):

```bash
runaway --visualize --steps 300 --agents 120 --preset small --floors 3 --stairs-mode default_stairs
```

`mesa[viz]` is installed by default via project dependencies.
If you use an older environment or hit dependency drift, refresh with:

```bash
pip install -U "mesa[viz]>=2.2,<3.0"
```

## Visualization (pygame desktop renderer)

Install optional dependency:

```bash
pip install -U "runaway[pygame]"
```

Run desktop visualization driven by simulation snapshots:

```bash
runaway --renderer pygame --steps 300 --agents 80 --preset small
```

Multifloor example with floor switching (`[` / `]` or arrow keys):

```bash
runaway --renderer pygame --steps 300 --agents 120 --preset small --floors 3 --stairs-mode default_stairs
```

Notes:
- `--visualize` still starts the Mesa browser renderer (reference adapter).
- `--renderer pygame` uses the same simulation core through `SimulationSnapshot`.

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

## Metrics and Experiment Scenarios

The project reports a stable set of run-level metrics:
- `steps_executed`
- `initial_agents`, `evacuated_agents`, `remaining_agents`
- `evacuation_ratio`, `fully_evacuated`
- `peak_remaining`, `avg_remaining`, `peak_evacuated`

Default experimental scenario matrix (`runaway.experiments.plan`):
- `light-load`: 80 agents, 250 steps, `small` preset
- `medium-load`: 180 agents, 320 steps, `small` preset
- `heavy-load`: 320 agents, 420 steps, `small` preset
- default seeds: `7, 11, 19, 23, 31`

## Exporting Single-Run Results

Export full time-series history and run summary directly from CLI:

```bash
runaway --steps 200 --agents 120 --preset small --seed 11 \
  --history-out artifacts/history.json \
  --summary-out artifacts/summary.json
```

History supports `.json` and `.csv` extensions.

## Batch Experiments (Reproducible Runs)

Run a batch for custom loads:

```bash
runaway-batch --output-dir artifacts/batch --agents-list 80,140,220 --steps 320 --preset small --seeds 7,11,19
```

Run the built-in scenario matrix:

```bash
runaway-batch --use-default-matrix --output-dir artifacts/batch-default
```

Batch outputs:
- `summary.csv`: one row per `scenario x seed` run with aggregate metrics
- `*_history.json`: full per-step time series for each run

## Methodology and Reproduction Checklist

1. Install dependencies with `make install-dev`.
2. Run `make check` to validate lint, formatting, and tests.
3. Generate experiment data with `runaway-batch`.
4. Use `summary.csv` for comparisons between scenarios/seeds.
5. Use `*_history.json` files for time-series plots in the report.

Model limitations to mention in report:
- Floor-aware abstraction with 4-neighborhood movement and stair transfer links.
- No explicit panic propagation/group behavior.
- Deterministic local movement policy based on static field.

## Custom visualization integration

Rendering is prepared as an adapter layer:
- simulation core exposes a floor-aware snapshot (`SimulationSnapshot`),
- Mesa browser UI acts as a reference adapter,
- custom visualization can consume snapshots without changing evacuation logic.

Current runtime options:
- `--floors` controls number of generated floors (default: `1`)
- `--stairs-mode` controls vertical links mode (currently: `default_stairs`)

## Authors
- Szymon Szarek
- Kamil Rudny