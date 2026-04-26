from importlib.resources import files

import pytest

from runaway.scenarios import build_d17, build_multifloor_d17


def test_d17_layout_full_contains_exits_and_spawns() -> None:
    walls, exits, spawn_points = build_d17(800, 453)

    assert len(exits) >= 500
    assert len(spawn_points) > 50_000
    assert len(walls) > 8_000
    assert exits.isdisjoint(walls)
    assert all(spawn not in walls for spawn in spawn_points)


def test_d17_layout_small_contains_exits_and_spawns() -> None:
    walls, exits, spawn_points = build_d17(320, 181)

    assert len(exits) >= 150
    assert len(spawn_points) >= 10_000
    assert len(walls) > 2_000
    assert exits.isdisjoint(walls)
    assert all(spawn not in walls for spawn in spawn_points)


def test_d17_exits_are_on_boundary_between_inside_and_outside() -> None:
    width, height = 800, 453
    walls, exits, _ = build_d17(width, height)
    walkable = {
        (x, y)
        for x in range(width)
        for y in range(height)
        if (x, y) not in walls and (x, y) not in exits
    }

    boundary_like = 0
    for x, y in exits:
        neighbors = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
        if any(n in walkable for n in neighbors):
            boundary_like += 1
    assert boundary_like > 0


def test_d17_layout_rejects_wrong_aspect_ratio() -> None:
    with pytest.raises(ValueError):
        build_d17(800, 200)

    with pytest.raises(ValueError):
        build_d17(400, 400)


def test_d17_layout_rejects_too_small_grid() -> None:
    with pytest.raises(ValueError):
        build_d17(50, 22)


def test_d17_exits_touch_walkable_interior() -> None:
    width, height = 800, 453
    walls, exits, _ = build_d17(width, height)

    walkable = {
        (x, y)
        for x in range(width)
        for y in range(height)
        if (x, y) not in walls and (x, y) not in exits
    }
    touching = 0
    for x, y in exits:
        neighbors = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
        if any(n in walkable for n in neighbors):
            touching += 1
    assert touching > 0


def test_d17_small_exits_touch_walkable_interior() -> None:
    width, height = 320, 181
    walls, exits, _ = build_d17(width, height)

    walkable = {
        (x, y)
        for x in range(width)
        for y in range(height)
        if (x, y) not in walls and (x, y) not in exits
    }
    touching = 0
    for x, y in exits:
        neighbors = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
        if any(n in walkable for n in neighbors):
            touching += 1
    assert touching > 0


def test_d17_wall_runs_json_is_packaged() -> None:
    resource = files("runaway.scenarios").joinpath("d17-wall-runs.json")
    assert resource.is_file()


def test_multifloor_d17_clones_layout_and_adds_stairs() -> None:
    floors, links = build_multifloor_d17(320, 181, 3, vertical_links_mode="default_stairs")

    assert len(floors) == 3
    assert floors[0].walls == floors[1].walls == floors[2].walls
    assert floors[0].exits == floors[1].exits == floors[2].exits
    assert links
    assert any(link.source[0] != link.target[0] for link in links)
