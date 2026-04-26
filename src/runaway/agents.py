from __future__ import annotations

from math import inf

from mesa import Agent

from runaway.floors import Cell3D


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


class EvacueeAgent(Agent):
    """A person attempting to reach the nearest exit."""

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

    def step(self) -> None:
        if self.position is None or self.evacuated:
            return

        model = self.model
        if self.position in model.exits:
            model.mark_evacuated(self)
            return

        neighbors = model.neighbors(self.position)
        candidates: list[tuple[Cell3D, float]] = []
        for nxt in neighbors:
            if nxt not in model.exits and model.is_occupied(nxt):
                continue
            candidates.append((nxt, model.field_value(nxt)))

        if not candidates:
            return

        current_score = model.field_value(self.position)
        best_score = min(score for _, score in candidates)

        if best_score >= current_score and current_score < inf:
            # Agent does not move if no neighbor improves current position.
            return

        best_cells = [cell for cell, score in candidates if score == best_score]
        target = self.random.choice(best_cells)
        model.move_agent(self, target)
