from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from heapq import heappop, heappush
from math import inf

from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid

from runaway.core.agents import EvacueeAgent, ExitCell, StairCell, WallCell
from runaway.core.config import SimulationConfig
from runaway.core.floors import Cell2D, Cell3D, TransferLink
from runaway.scenarios import build_multifloor_d17
from runaway.statistics.collector import MetricsCollector
from runaway.statistics.writer import CsvResultsWriter


@dataclass(frozen=True, slots=True)
class AgentSnapshot:
    unique_id: int
    position: Cell3D
    evacuated: bool


@dataclass(frozen=True, slots=True)
class SimulationSnapshot:
    step: int
    evacuated: int
    remaining: int
    floors_count: int
    walls: dict[int, set[Cell2D]]
    exits: dict[int, set[Cell2D]]
    transfer_nodes: dict[int, set[Cell2D]]
    agents: list[AgentSnapshot]


class EvacuationModel(Model):
    """Mesa model for a floor-aware evacuation simulation."""

    def __init__(
        self,
        config: SimulationConfig,
        metrics_collector: MetricsCollector | None = None,
    ) -> None:
        super().__init__(seed=config.seed)
        self.config = config
        self.run_id: str = datetime.now().isoformat()
        self.metrics = metrics_collector or MetricsCollector()
        self._writer = CsvResultsWriter()
        self._results_saved = False
        self.grid = MultiGrid(config.width, config.height * config.floors_count, torus=False)

        self.floor_specs, self.transfer_links = build_multifloor_d17(
            config.width,
            config.height,
            config.floors_count,
            vertical_links_mode=config.vertical_links_mode,
            stair_traversal_cost=config.stair_traversal_cost,
        )
        self.walls_by_floor = {spec.level: set(spec.walls) for spec in self.floor_specs}
        self.exits_by_floor = {spec.level: set(spec.exits) for spec in self.floor_specs}
        self.walkable = {
            (spec.level, x, y)
            for spec in self.floor_specs
            for x in range(config.width)
            for y in range(config.height)
            if (x, y) not in spec.walls
        }
        self.exits = {(spec.level, x, y) for spec in self.floor_specs for x, y in spec.exits}
        self.transfer_graph = self._build_transfer_graph(self.transfer_links)
        self.transfer_nodes_by_floor = self._transfer_nodes_per_floor(self.transfer_links)
        spawn_points = [
            (spec.level, x, y) for spec in self.floor_specs for x, y in spec.spawn_points
        ]

        if config.n_agents > len(spawn_points):
            raise ValueError("n_agents exceeds available spawn cells for this floor plan")

        shuffled = spawn_points[:]
        self.random.shuffle(shuffled)

        self._active_agents: list[EvacueeAgent] = []
        self._occupancy: dict[Cell3D, EvacueeAgent] = {}

        self.initial_agents = config.n_agents
        self.evacuated_count = 0
        self.step_count = 0
        self.history: list[dict[str, int]] = []

        self.static_field = self._compute_static_field()

        # Place static markers for browser visualization on all floors.
        for floor in range(config.floors_count):
            for x, y in self.walls_by_floor.get(floor, set()):
                self.grid.place_agent(
                    WallCell(f"wall-{floor}-{x}-{y}", self), self.to_grid_pos((floor, x, y))
                )
            for x, y in self.exits_by_floor.get(floor, set()):
                self.grid.place_agent(
                    ExitCell(f"exit-{floor}-{x}-{y}", self), self.to_grid_pos((floor, x, y))
                )
            for x, y in self.transfer_nodes_by_floor.get(floor, set()):
                self.grid.place_agent(
                    StairCell(f"stair-{floor}-{x}-{y}", self), self.to_grid_pos((floor, x, y))
                )

        for idx in range(config.n_agents):
            start = shuffled[idx]
            agent = EvacueeAgent(idx, self, start)
            agent.start_floor = start[0]
            self._active_agents.append(agent)
            self._occupancy[start] = agent
            self.grid.place_agent(agent, self.to_grid_pos(start))

        # Mesa DataCollector for standard reporters
        model_reporters: dict[str, Callable] = {
            "Evacuated": lambda m: m.evacuated_count,
            "Remaining": lambda m: m.active_agents,
            "EvacuationPct": lambda m: (
                m.evacuated_count / m.initial_agents * 100 if m.initial_agents > 0 else 0.0
            ),
        }
        for floor_idx in range(config.floors_count):
            floor_idx_copy = floor_idx
            model_reporters[f"Floor{floor_idx}_Remaining"] = lambda m, f=floor_idx_copy: sum(
                1 for a in m._active_agents if a.position is not None and a.position[0] == f
            )
        self.datacollector = DataCollector(model_reporters=model_reporters)

        self._record_metrics()
        self.running = False
        self.latest_snapshot = self.snapshot()

    @property
    def active_agents(self) -> int:
        return len(self._active_agents)

    @property
    def occupied_cells(self) -> set[Cell3D]:
        return set(self._occupancy.keys())

    def _build_transfer_graph(
        self, links: list[TransferLink]
    ) -> dict[Cell3D, list[tuple[Cell3D, int]]]:
        graph: dict[Cell3D, list[tuple[Cell3D, int]]] = {}
        for link in links:
            graph.setdefault(link.source, []).append((link.target, link.cost))
            if link.bidirectional:
                graph.setdefault(link.target, []).append((link.source, link.cost))
        return graph

    def _transfer_nodes_per_floor(self, links: list[TransferLink]) -> dict[int, set[Cell2D]]:
        result: dict[int, set[Cell2D]] = {spec.level: set() for spec in self.floor_specs}
        for link in links:
            sf, sx, sy = link.source
            tf, tx, ty = link.target
            result.setdefault(sf, set()).add((sx, sy))
            result.setdefault(tf, set()).add((tx, ty))
        return result

    def _record_metrics(self) -> None:
        self.history.append(
            {
                "step": self.step_count,
                "evacuated": self.evacuated_count,
                "remaining": self.active_agents,
            }
        )
        self.metrics.on_step(self)
        self.datacollector.collect(self)

    def _compute_static_field(self) -> dict[Cell3D, float]:
        """Compute shortest path distance to the nearest exit across all floors."""
        distance = {cell: inf for cell in self.walkable}
        heap: list[tuple[float, Cell3D]] = []

        for ex in self.exits:
            if ex in distance:
                distance[ex] = 0
                heappush(heap, (0, ex))

        while heap:
            base, cell = heappop(heap)
            if base > distance[cell]:
                continue
            for nxt, cost in self.edges_from(cell):
                if nxt not in distance:
                    continue
                candidate = base + cost
                if candidate < distance[nxt]:
                    distance[nxt] = candidate
                    heappush(heap, (candidate, nxt))

        return distance

    def to_grid_pos(self, pos: Cell3D) -> Cell2D:
        floor, x, y = pos
        return x, floor * self.config.height + y

    def in_bounds(self, pos: Cell3D) -> bool:
        floor, x, y = pos
        return (
            0 <= floor < self.config.floors_count
            and 0 <= x < self.config.width
            and 0 <= y < self.config.height
        )

    def neighbors(self, pos: Cell3D) -> list[Cell3D]:
        floor, x, y = pos
        candidates = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        planar = [
            (floor, nx, ny)
            for nx, ny in candidates
            if self.in_bounds((floor, nx, ny)) and (nx, ny) not in self.walls_by_floor[floor]
        ]
        vertical = [target for target, _ in self.transfer_graph.get(pos, [])]
        return planar + vertical

    def edges_from(self, pos: Cell3D) -> list[tuple[Cell3D, int]]:
        floor, x, y = pos
        candidates = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        planar_edges = [
            ((floor, nx, ny), 1)
            for nx, ny in candidates
            if self.in_bounds((floor, nx, ny)) and (nx, ny) not in self.walls_by_floor[floor]
        ]
        return planar_edges + list(self.transfer_graph.get(pos, []))

    def is_occupied(self, pos: Cell3D) -> bool:
        return pos in self._occupancy

    def field_value(self, pos: Cell3D) -> float:
        return self.static_field.get(pos, inf)

    def transfer_cost(self, source: Cell3D, target: Cell3D) -> int:
        """Return the traversal cost between two connected cells."""
        for dest, cost in self.transfer_graph.get(source, []):
            if dest == target:
                return cost
        return 1

    def move_agent(self, agent: EvacueeAgent, target: Cell3D) -> bool:
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
            self.grid.move_agent(agent, self.to_grid_pos(target))
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
        agent.evacuation_step = self.step_count
        self.evacuated_count += 1
        self._active_agents = [a for a in self._active_agents if a is not agent]
        self.metrics.on_agent_evacuated(agent, self.step_count)

    def step(self) -> None:
        # Only run agent logic when the simulation is still in progress.
        if self.active_agents > 0 and self.step_count < self.config.max_steps:
            activation_order = self._active_agents[:]
            # Process agents closest to exit first so vacated cells cascade back.
            activation_order.sort(key=lambda a: self.static_field.get(a.position, inf))

            for agent in activation_order:
                if not agent.evacuated:
                    agent.step()

            self.step_count += 1
            self._record_metrics()
            self.latest_snapshot = self.snapshot()

        # Check termination — save results exactly once, then stop.
        if self.active_agents == 0 or self.step_count >= self.config.max_steps:
            if not self._results_saved:
                self._writer.save(self.run_id, self.config, self.metrics)
                self._results_saved = True
                print(f"Results saved to results/sim_{self.run_id.replace(':', '-')}/")
            self.running = False

    def run(self) -> None:
        self.running = True
        while self.running:
            self.step()

    def snapshot(self) -> SimulationSnapshot:
        return SimulationSnapshot(
            step=self.step_count,
            evacuated=self.evacuated_count,
            remaining=self.active_agents,
            floors_count=self.config.floors_count,
            walls={floor: set(walls) for floor, walls in self.walls_by_floor.items()},
            exits={floor: set(exits) for floor, exits in self.exits_by_floor.items()},
            transfer_nodes={
                floor: set(nodes) for floor, nodes in self.transfer_nodes_by_floor.items()
            },
            agents=[
                AgentSnapshot(
                    unique_id=int(agent.unique_id),
                    position=agent.position,
                    evacuated=agent.evacuated,
                )
                for agent in self._active_agents
                if agent.position is not None
            ],
        )
