from __future__ import annotations

import argparse
from pathlib import Path

from runaway.cli.grid_presets import _PRESETS, adaptive_visualization_grid
from runaway.core.config import SimulationConfig
from runaway.experiments.results import (
    compute_summary_metrics,
    write_history_csv,
    write_history_json,
    write_summary_json,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a building evacuation simulation.")
    parser.add_argument("--width", type=int, default=None, help="Grid width")
    parser.add_argument("--height", type=int, default=None, help="Grid height")
    parser.add_argument(
        "--preset",
        choices=[*list(_PRESETS), "auto"],
        default=None,
        help=(
            "Grid size preset: 'full' (800x453), 'small' (320x181), "
            "or 'auto' (adaptive for browser viz)"
        ),
    )
    parser.add_argument("--agents", type=int, default=60, help="Number of evacuee agents")
    parser.add_argument("--steps", type=int, default=300, help="Maximum simulation steps")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--floors", type=int, default=1, help="Number of floors")
    parser.add_argument(
        "--stairs-mode",
        choices=["default_stairs"],
        default="default_stairs",
        help="Vertical transfer links mode between floors",
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Run Mesa browser visualization server",
    )
    parser.add_argument(
        "--renderer",
        choices=["none", "mesa", "pygame"],
        default="none",
        help="Visualization backend: none, mesa (browser), or pygame (desktop)",
    )
    parser.add_argument("--port", type=int, default=8521, help="Visualization server port")
    parser.add_argument(
        "--history-out",
        type=Path,
        default=None,
        help="Optional path for simulation history export (.json or .csv)",
    )
    parser.add_argument(
        "--summary-out",
        type=Path,
        default=None,
        help="Optional path for run summary metrics export (JSON)",
    )
    return parser


def _adaptive_visualization_grid() -> tuple[int, int]:
    return adaptive_visualization_grid()


def resolve_grid_size(args: argparse.Namespace) -> tuple[int, int]:
    if args.preset:
        if args.preset == "auto":
            return _adaptive_visualization_grid()
        return _PRESETS[args.preset]

    if args.width is not None and args.height is not None:
        return args.width, args.height

    if args.visualize or args.renderer == "mesa":
        return _adaptive_visualization_grid()

    return _PRESETS["full"]


def _write_history(history_path: Path, history: list[dict[str, int]]) -> None:
    if history_path.suffix.lower() == ".csv":
        write_history_csv(history, history_path)
        return
    write_history_json(history, history_path)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if (args.width is None) != (args.height is None):
        parser.error("--width and --height must be provided together")
    if args.floors < 1:
        parser.error("--floors must be >= 1")
    if args.visualize and args.renderer == "pygame":
        parser.error("--visualize cannot be used together with --renderer pygame")

    w, h = resolve_grid_size(args)

    config = SimulationConfig(
        width=w,
        height=h,
        n_agents=args.agents,
        max_steps=args.steps,
        seed=args.seed,
        floors_count=args.floors,
        vertical_links_mode=args.stairs_mode,
    )

    renderer = "mesa" if args.visualize else args.renderer

    if renderer == "mesa":
        from runaway.renderers.mesa import launch_server

        launch_server(config, port=args.port)
        return
    if renderer == "pygame":
        from runaway.renderers.pygame import launch_pygame

        launch_pygame(config)
        return

    from runaway.core.model import EvacuationModel

    model = EvacuationModel(config)
    model.run()
    summary = compute_summary_metrics(model)

    if args.history_out is not None:
        _write_history(args.history_out, model.history)
        print(f"Saved history: {args.history_out}")
    if args.summary_out is not None:
        write_summary_json(summary, args.summary_out)
        print(f"Saved summary: {args.summary_out}")

    print(f"Steps executed: {model.step_count}")
    print(f"Evacuated agents: {model.evacuated_count}/{model.initial_agents}")
    print(f"Remaining agents: {model.active_agents}")


if __name__ == "__main__":
    main()
