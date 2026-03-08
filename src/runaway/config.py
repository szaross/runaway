from dataclasses import dataclass


@dataclass(slots=True)
class SimulationConfig:
    width: int = 25
    height: int = 18
    n_agents: int = 60
    max_steps: int = 300
    seed: int | None = None
