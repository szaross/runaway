from __future__ import annotations

import math
from math import inf

from mesa import Agent

from runaway.core.floors import Cell3D


class WallCell(Agent):
    """Static wall marker used only for visualization."""

    def __init__(self, unique_id: str, model) -> None:
        try:
            super().__init__(unique_id, model)
        except TypeError:
            super().__init__(model)
            self.unique_id = unique_id


class ExitCell(Agent):
    """Static exit marker used only for visualization."""

    def __init__(self, unique_id: str, model) -> None:
        try:
            super().__init__(unique_id, model)
        except TypeError:
            super().__init__(model)
            self.unique_id = unique_id


class StairCell(Agent):
    """Static staircase marker used only for visualization."""

    def __init__(self, unique_id: str, model) -> None:
        try:
            super().__init__(unique_id, model)
        except TypeError:
            super().__init__(model)
            self.unique_id = unique_id


class EvacueeAgent(Agent):
    """A person attempting to reach the nearest exit."""

    # Temperature for Boltzmann selection: higher = more random, lower = more greedy
    _TEMPERATURE = 1.5
    # Penalty per occupied neighbour — discourages crowded corridors
    _CONGESTION_WEIGHT = 1.2

    def __init__(
        self,
        unique_id: int,
        model,
        start_pos: Cell3D,
    ) -> None:
        try:
            super().__init__(unique_id, model)
        except TypeError:
            super().__init__(model)
            self.unique_id = unique_id

        self.position: Cell3D | None = start_pos
        self.evacuated = False
        self.start_floor: int | None = None
        self.steps_taken: int = 0
        self.evacuation_step: int | None = None
        self._stair_delay: int = 0

    def _congestion_at(self, pos: Cell3D) -> int:
        model = self.model
        return sum(1 for n in model.neighbors(pos) if model.is_occupied(n))

    def step(self) -> None:
        if self.position is None or self.evacuated:
            return

        model = self.model
        if self.position in model.exits:
            model.mark_evacuated(self)
            return

        # Wait out stair traversal delay
        if self._stair_delay > 0:
            self._stair_delay -= 1
            self.steps_taken += 1
            return

        neighbors = model.neighbors(self.position)
        candidates: list[tuple[Cell3D, float]] = []
        for nxt in neighbors:
            if nxt not in model.exits and model.is_occupied(nxt):
                continue
            score = model.field_value(nxt) + self._CONGESTION_WEIGHT * self._congestion_at(nxt)
            candidates.append((nxt, score))

        if not candidates:
            return

        # Only consider moves that improve on current position (don't wander endlessly).
        current_distance = model.field_value(self.position)
        improving = [(cell, score) for cell, score in candidates if model.field_value(cell) < current_distance]
        pool = improving if improving else candidates

        # Boltzmann selection: lower score = higher probability.
        min_score = min(score for _, score in pool)
        weights = [math.exp(-(score - min_score) / self._TEMPERATURE) for _, score in pool]
        total = sum(weights)

        r = self.random.random() * total
        cumulative = 0.0
        target = pool[0][0]
        for (cell, _), w in zip(pool, weights):
            cumulative += w
            if r <= cumulative:
                target = cell
                break

        # Apply stair traversal delay for cross-floor moves
        if target[0] != self.position[0]:
            cost = model.transfer_cost(self.position, target)
            if cost > 1:
                self._stair_delay = cost - 1

        self.steps_taken += 1
        model.move_agent(self, target)

