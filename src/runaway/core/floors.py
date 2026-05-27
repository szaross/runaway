from __future__ import annotations

from dataclasses import dataclass

Cell2D = tuple[int, int]
Cell3D = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class FloorSpec:
    level: int
    walls: set[Cell2D]
    exits: set[Cell2D]
    spawn_points: list[Cell2D]


@dataclass(frozen=True, slots=True)
class TransferLink:
    source: Cell3D
    target: Cell3D
    cost: int = 1
    bidirectional: bool = True
