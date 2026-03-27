from __future__ import annotations

from collections import deque
from math import inf

from mesa import Model
from mesa.space import MultiGrid

from runaway.agents import EvacueeAgent, ExitCell, WallCell
from runaway.config import SimulationConfig
from runaway.scenarios import build_d17


class EvacuationModel(Model):
    """Mesa model for a single-floor evacuation simulation."""

    def __init__(self, config: SimulationConfig) -> None:
        super().__init__(seed=config.seed)
        self.config = config
        self.grid = MultiGrid(config.width, config.height, torus=False)

        self.walls, self.exits, spawn_points = build_d17(config.width, config.height)
        self.walkable = {
            (x, y)
            for x in range(config.width)
            for y in range(config.height)
            if (x, y) not in self.walls
        }

        if config.n_agents > len(spawn_points):
            raise ValueError("n_agents exceeds available spawn cells for this floor plan")

        shuffled = spawn_points[:]
        self.random.shuffle(shuffled)

        self._active_agents: list[EvacueeAgent] = []
        self._occupancy: dict[tuple[int, int], EvacueeAgent] = {}

        self.initial_agents = config.n_agents
        self.evacuated_count = 0
        self.step_count = 0
        self.history: list[dict[str, int]] = []

        self.static_field = self._compute_static_field()

        # Place static markers for browser visualization.
        for x, y in self.walls:
            self.grid.place_agent(WallCell(f"wall-{x}-{y}", self), (x, y))

        for x, y in self.exits:
            self.grid.place_agent(ExitCell(f"exit-{x}-{y}", self), (x, y))

        for idx in range(config.n_agents):
            start = shuffled[idx]
            agent = EvacueeAgent(idx, self, start)
            self._active_agents.append(agent)
            self._occupancy[start] = agent
            self.grid.place_agent(agent, start)

        self._record_metrics()
        self.running = False

    @property
    def active_agents(self) -> int:
        return len(self._active_agents)

    @property
    def occupied_cells(self) -> set[tuple[int, int]]:
        return set(self._occupancy.keys())

    def _record_metrics(self) -> None:
        self.history.append(
            {
                "step": self.step_count,
                "evacuated": self.evacuated_count,
                "remaining": self.active_agents,
            }
        )

    def _compute_static_field(self) -> dict[tuple[int, int], int]:
        """Compute shortest path distance to the nearest exit for each walkable cell."""
        distance = {cell: inf for cell in self.walkable}
        queue: deque[tuple[int, int]] = deque()

        for ex in self.exits:
            if ex in distance:
                distance[ex] = 0
                queue.append(ex)

        while queue:
            cell = queue.popleft()
            base = distance[cell]
            for nxt in self.neighbors4(cell):
                if nxt not in distance:
                    continue
                if distance[nxt] > base + 1:
                    distance[nxt] = base + 1
                    queue.append(nxt)

        return distance

    def in_bounds(self, pos: tuple[int, int]) -> bool:
        x, y = pos
        return 0 <= x < self.config.width and 0 <= y < self.config.height

    def neighbors4(self, pos: tuple[int, int]) -> list[tuple[int, int]]:
        x, y = pos
        candidates = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        return [p for p in candidates if self.in_bounds(p) and p not in self.walls]

    def is_occupied(self, pos: tuple[int, int]) -> bool:
        return pos in self._occupancy

    def field_value(self, pos: tuple[int, int]) -> float:
        return self.static_field.get(pos, inf)

    def move_agent(self, agent: EvacueeAgent, target: tuple[int, int]) -> bool:
        current = agent.position
        if current is None:
            return False

        if target not in self.walkable:
            return False
        if target != current and target not in self.exits and self.is_occupied(target):
            return False

        if current in self._occupancy:
            del self._occupancy[current]
        if current != target:
            self.grid.move_agent(agent, target)
        agent.position = target

        if target in self.exits:
            self.mark_evacuated(agent)
            return True

        self._occupancy[target] = agent
        return True

    def mark_evacuated(self, agent: EvacueeAgent) -> None:
        if agent.evacuated:
            return

        current = agent.position
        if current is not None and current in self._occupancy:
            del self._occupancy[current]
        if current is not None:
            self.grid.remove_agent(agent)

        agent.position = None
        agent.evacuated = True
        self.evacuated_count += 1
        self._active_agents = [a for a in self._active_agents if a is not agent]

    def step(self) -> None:
        if self.active_agents == 0 or self.step_count >= self.config.max_steps:
            self.running = False
            return

        activation_order = self._active_agents[:]
        self.random.shuffle(activation_order)

        for agent in activation_order:
            if not agent.evacuated:
                agent.step()

        self.step_count += 1
        self._record_metrics()

        if self.active_agents == 0 or self.step_count >= self.config.max_steps:
            self.running = False

    def run(self) -> None:
        self.running = True
        while self.running:
            self.step()
