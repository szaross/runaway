from dataclasses import dataclass


@dataclass(slots=True)
class SimulationConfig:
    width: int = 800
    height: int = 453
    n_agents: int = 60
    max_steps: int = 300
    seed: int | None = None
    floors_count: int = 1
    vertical_links_mode: str = "default_stairs"
