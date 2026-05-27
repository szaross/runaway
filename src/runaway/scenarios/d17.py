from __future__ import annotations

import json
from collections import deque
from functools import lru_cache
from importlib.resources import as_file, files
from typing import Any

from runaway.floors import FloorSpec, TransferLink

_BASE_WIDTH = 2938
_BASE_HEIGHT = 1662
_MIN_WIDTH = 160
_MIN_HEIGHT = 90


def _validate_grid(width: int, height: int) -> None:
    if width < _MIN_WIDTH or height < _MIN_HEIGHT:
        raise ValueError(f"D17 layout requires at least {_MIN_WIDTH}x{_MIN_HEIGHT} grid.")

    # Keep D17 aspect ratio from the source wall-runs with small scaling tolerance.
    ratio_error = abs(width * _BASE_HEIGHT - height * _BASE_WIDTH)
    tolerance = max(_BASE_HEIGHT, width * _BASE_HEIGHT // 80)
    if ratio_error > tolerance:
        raise ValueError(
            f"D17 layout expects approximately {_BASE_WIDTH}:{_BASE_HEIGHT} aspect ratio."
        )


def _scale_x(x: int, width: int) -> int:
    return round(x * (width - 1) / (_BASE_WIDTH - 1))


def _scale_y(y: int, height: int) -> int:
    # Image coordinates grow downward; Mesa grid grows upward.
    return round(((_BASE_HEIGHT - 1) - y) * (height - 1) / (_BASE_HEIGHT - 1))


@lru_cache(maxsize=1)
def _load_wall_runs_payload() -> dict[str, Any]:
    payload: dict[str, Any] | None = None
    resource = files("runaway.scenarios").joinpath("d17-wall-runs.json")
    try:
        with as_file(resource) as data_path:
            with data_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
    except FileNotFoundError:
        payload = None

    if payload is None:
        raise FileNotFoundError("Missing packaged D17 wall-runs JSON in runaway.scenarios.")

    if payload.get("encoding") != "wall-runs-rb-v1":
        raise ValueError("Unsupported D17 wall-runs encoding.")
    if int(payload.get("width", 0)) != _BASE_WIDTH or int(payload.get("height", 0)) != _BASE_HEIGHT:
        raise ValueError("Unexpected D17 wall-runs base resolution.")
    return payload


def _scale_runs_to_cells(runs: list[list[int]], width: int, height: int) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for y, x_start, x_end in runs:
        sy = _scale_y(int(y), height)
        sx0 = _scale_x(int(x_start), width)
        sx1 = _scale_x(int(x_end), width)
        if sx1 < sx0:
            sx0, sx1 = sx1, sx0
        for sx in range(sx0, sx1 + 1):
            cells.add((sx, sy))
    return cells


def _interior_cells(
    width: int, height: int, walls: set[tuple[int, int]], exits: set[tuple[int, int]]
) -> set[tuple[int, int]]:
    blocked = walls | exits
    outside: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()

    for x in range(width):
        for y in (0, height - 1):
            if (x, y) not in blocked and (x, y) not in outside:
                outside.add((x, y))
                queue.append((x, y))
    for y in range(height):
        for x in (0, width - 1):
            if (x, y) not in blocked and (x, y) not in outside:
                outside.add((x, y))
                queue.append((x, y))

    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if not (0 <= nx < width and 0 <= ny < height):
                continue
            if (nx, ny) in blocked or (nx, ny) in outside:
                continue
            outside.add((nx, ny))
            queue.append((nx, ny))

    return {
        (x, y)
        for x in range(width)
        for y in range(height)
        if (x, y) not in blocked and (x, y) not in outside
    }


def build_d17(
    width: int, height: int
) -> tuple[set[tuple[int, int]], set[tuple[int, int]], list[tuple[int, int]]]:
    """Build D17 floor layout from wall-runs: walls, exits, and spawn points."""
    _validate_grid(width, height)
    payload = _load_wall_runs_payload()

    walls = _scale_runs_to_cells(payload["red_runs"], width, height)
    exits = _scale_runs_to_cells(payload["blue_runs"], width, height)
    walls -= exits

    inside_cells = _interior_cells(width, height, walls, exits)
    spawn_points = sorted(inside_cells)

    if not exits:
        raise ValueError("D17 layout produced no exits.")
    if len(spawn_points) < 20:
        raise ValueError("D17 layout produced too few spawn cells.")

    return walls, exits, spawn_points


def _default_stair_cells(
    spawn_points: list[tuple[int, int]],
    width: int,
    height: int,
) -> list[tuple[int, int]]:
    """Create a single staircase block in the center of the building interior."""
    if len(spawn_points) < 4:
        raise ValueError("D17 layout produced too few spawn cells for stairs.")

    spawn_set = set(spawn_points)

    # Find the center of mass of interior cells
    cx = 117
    cy = 140

    # Find the closest spawn cell to center
    center = min(spawn_points, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)
    stair_radius = 2
    expanded: set[tuple[int, int]] = set()
    for dx in range(-stair_radius, stair_radius + 1):
        for dy in range(-stair_radius, stair_radius + 1):
            nx, ny = center[0] + dx, center[1] + dy
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) in spawn_set:
                expanded.add((nx, ny))

    return sorted(expanded)


# Hardcoded position for the second staircase (grid coordinates, origin at bottom-left).
# Change these two values to reposition the staircase.
# Spawn cells exist roughly in X: 56–768, Y: 80–411.
_STAIR2_X = 245
_STAIR2_Y = 406


def _second_stair_cells(
    spawn_points: list[tuple[int, int]],
    width: int,
    height: int,
) -> list[tuple[int, int]]:
    """Create a second staircase block anchored at (_STAIR2_X, _STAIR2_Y).

    Snapping strategy: find cells in the closest Y band first, then pick
    the one nearest in X. This ensures X and Y are controlled independently.
    """
    if len(spawn_points) < 4:
        raise ValueError("D17 layout produced too few spawn cells for stairs.")

    spawn_set = set(spawn_points)

    # Expand search band until we find candidates (handles sparse upper/lower areas)
    band = 5
    candidates: list[tuple[int, int]] = []
    while not candidates and band <= max(width, height):
        candidates = [p for p in spawn_points if abs(p[1] - _STAIR2_Y) <= band]
        band *= 2

    anchor = min(candidates, key=lambda p: abs(p[0] - _STAIR2_X))

    stair_radius = 2
    expanded: set[tuple[int, int]] = set()
    for dx in range(-stair_radius, stair_radius + 1):
        for dy in range(-stair_radius, stair_radius + 1):
            nx, ny = anchor[0] + dx, anchor[1] + dy
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) in spawn_set:
                expanded.add((nx, ny))

    return sorted(expanded)


def build_multifloor_d17(
    width: int,
    height: int,
    floors_count: int,
    *,
    vertical_links_mode: str = "default_stairs",
    stair_traversal_cost: int = 1,
) -> tuple[list[FloorSpec], list[TransferLink]]:
    if floors_count < 1:
        raise ValueError("floors_count must be >= 1")
    if vertical_links_mode != "default_stairs":
        raise ValueError("Unsupported vertical links mode.")

    base_walls, base_exits, base_spawn_points = build_d17(width, height)
    # On upper floors, exit positions become walls (no gaps).
    upper_walls = base_walls | base_exits
    floor_specs = [
        FloorSpec(
            level=floor,
            walls=set(base_walls) if floor == 0 else set(upper_walls),
            exits=set(base_exits) if floor == 0 else set(),
            spawn_points=list(base_spawn_points),
        )
        for floor in range(floors_count)
    ]

    all_stair_cells = _default_stair_cells(base_spawn_points, width, height) + _second_stair_cells(
        base_spawn_points, width, height
    )
    transfer_links: list[TransferLink] = []
    for lower_floor in range(floors_count - 1):
        upper_floor = lower_floor + 1
        for x, y in all_stair_cells:
            transfer_links.append(
                TransferLink(
                    source=(lower_floor, x, y),
                    target=(upper_floor, x, y),
                    cost=stair_traversal_cost,
                    bidirectional=True,
                )
            )

    return floor_specs, transfer_links
