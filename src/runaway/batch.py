from __future__ import annotations

import argparse
import csv
from pathlib import Path

from runaway.cli import _PRESETS, _adaptive_visualization_grid
from runaway.config import SimulationConfig
from runaway.experiment_plan import DEFAULT_SEEDS, SCENARIO_MATRIX, ScenarioDefinition
from runaway.model import EvacuationModel
from runaway.results import compute_summary_metrics, write_history_json


def _parse_int_list(raw: str) -> list[int]:
    return [int(part.strip()) for part in raw.split(",") if part.strip()]


def _resolve_grid(preset: str) -> tuple[int, int]:
    if preset == "auto":
        return _adaptive_visualization_grid()
    return _PRESETS[preset]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run batches of evacuation simulations.")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/batch"))
    parser.add_argument("--agents-list", type=str, default="")
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--preset", choices=[*list(_PRESETS), "auto"], default="small")
    parser.add_argument("--seeds", type=str, default="")
    parser.add_argument(
        "--use-default-matrix",
        action="store_true",
        help="Use built-in scenario matrix instead of custom --agents-list",
    )
    return parser


def _run_single(
    output_dir: Path, *, name: str, config: SimulationConfig, seed: int
) -> dict[str, float | int | str]:
    model = EvacuationModel(config)
    model.run()
    summary = compute_summary_metrics(model)

    history_path = output_dir / f"{name}_seed-{seed}_history.json"
    write_history_json(model.history, history_path)

    return {
        "scenario": name,
        "seed": seed,
        "width": config.width,
        "height": config.height,
        "agents": config.n_agents,
        "max_steps": config.max_steps,
        **summary,
    }


def _write_summary_csv(rows: list[dict[str, float | int | str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        output_path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = build_parser().parse_args()
    seeds = _parse_int_list(args.seeds) if args.seeds else list(DEFAULT_SEEDS)
    rows: list[dict[str, float | int | str]] = []
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.use_default_matrix:
        scenarios: list[ScenarioDefinition] = list(SCENARIO_MATRIX)
    else:
        agents = _parse_int_list(args.agents_list) if args.agents_list else [60, 120, 180, 240]
        scenarios = [
            ScenarioDefinition(
                name=f"agents-{count}", agents=count, steps=args.steps, preset=args.preset
            )
            for count in agents
        ]

    for scenario in scenarios:
        width, height = _resolve_grid(scenario.preset)
        for seed in seeds:
            config = SimulationConfig(
                width=width,
                height=height,
                n_agents=scenario.agents,
                max_steps=scenario.steps,
                seed=seed,
            )
            rows.append(_run_single(output_dir, name=scenario.name, config=config, seed=seed))

    summary_csv = output_dir / "summary.csv"
    _write_summary_csv(rows, summary_csv)
    print(f"Saved batch summary: {summary_csv}")
    print(f"Saved per-run histories in: {output_dir}")


if __name__ == "__main__":
    main()
