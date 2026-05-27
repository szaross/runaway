from dataclasses import dataclass

_MAX_FLOORS = 4


@dataclass(slots=True)
class SimulationConfig:
    width: int = 800
    height: int = 453
    n_agents: int = 60
    max_steps: int = 300
    seed: int | None = None
    floors_count: int = 1
    vertical_links_mode: str = "default_stairs"
    stair_traversal_cost: int | None = None

    def __post_init__(self) -> None:
        if self.floors_count < 1 or self.floors_count > _MAX_FLOORS:
            raise ValueError(f"floors_count must be between 1 and {_MAX_FLOORS}")
        if self.stair_traversal_cost is None:
            self.stair_traversal_cost = max(1, self.height // 45)
