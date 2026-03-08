from __future__ import annotations

import argparse

from runaway.config import SimulationConfig
from runaway.model import EvacuationModel


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a building evacuation simulation.")
    parser.add_argument("--width", type=int, default=25, help="Grid width")
    parser.add_argument("--height", type=int, default=18, help="Grid height")
    parser.add_argument("--agents", type=int, default=60, help="Number of evacuee agents")
    parser.add_argument("--steps", type=int, default=300, help="Maximum simulation steps")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = SimulationConfig(
        width=args.width,
        height=args.height,
        n_agents=args.agents,
        max_steps=args.steps,
        seed=args.seed,
    )

    model = EvacuationModel(config)
    model.run()

    print(f"Steps executed: {model.step_count}")
    print(f"Evacuated agents: {model.evacuated_count}/{model.initial_agents}")
    print(f"Remaining agents: {model.active_agents}")


if __name__ == "__main__":
    main()
