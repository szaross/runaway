from __future__ import annotations

from mesa import Model

from runaway.config import SimulationConfig


class EvacuationModel(Model):
    """Mesa model for a single-floor evacuation simulation."""

    def __init__(self, config: SimulationConfig) -> None:
        self.running = False

    def step(self) -> None:
        pass

    def run(self) -> None:
        self.running = True
        while self.running:
            self.step()
