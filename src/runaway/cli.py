from __future__ import annotations

import argparse

from runaway.config import SimulationConfig

_PRESETS = {
    "full": (800, 453),
    "small": (320, 181),
}
_MAX_VIZ_CELLS = 70_000


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
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Run Mesa browser visualization server",
    )
    parser.add_argument("--port", type=int, default=8521, help="Visualization server port")
    return parser


def _adaptive_visualization_grid() -> tuple[int, int]:
    """Pick the densest browser-friendly grid preserving D17 aspect ratio."""
    full_w, full_h = _PRESETS["full"]
    if full_w * full_h <= _MAX_VIZ_CELLS:
        return full_w, full_h

    scale = (_MAX_VIZ_CELLS / (full_w * full_h)) ** 0.5
    width = max(_PRESETS["small"][0], int(full_w * scale))
    height = round(width * full_h / full_w)
    return width, height


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if (args.width is None) != (args.height is None):
        parser.error("--width and --height must be provided together")

    if args.preset:
        if args.preset == "auto":
            w, h = _adaptive_visualization_grid()
        else:
            w, h = _PRESETS[args.preset]
    elif args.width is not None and args.height is not None:
        w, h = args.width, args.height
    elif args.visualize:
        w, h = _adaptive_visualization_grid()
    else:
        w, h = _PRESETS["full"]

    config = SimulationConfig(
        width=w,
        height=h,
        n_agents=args.agents,
        max_steps=args.steps,
        seed=args.seed,
    )

    if args.visualize:
        from runaway.visualization import launch_server

        launch_server(config, port=args.port)
        return

    from runaway.model import EvacuationModel

    model = EvacuationModel(config)
    model.run()

    print(f"Steps executed: {model.step_count}")
    print(f"Evacuated agents: {model.evacuated_count}/{model.initial_agents}")
    print(f"Remaining agents: {model.active_agents}")


if __name__ == "__main__":
    main()
