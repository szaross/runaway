from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from runaway.model import SimulationSnapshot


class RendererAdapter(Protocol):
    def render(self, snapshot: SimulationSnapshot) -> None:
        """Consume simulation snapshot and render it."""


@dataclass(slots=True)
class NullRendererAdapter:
    """Reference renderer used in non-visual runs/tests."""

    def render(self, snapshot: SimulationSnapshot) -> None:  # pragma: no cover - trivial
        _ = snapshot
