from __future__ import annotations

import json

import pytest

pytest.importorskip("PIL")
from PIL import Image

from runaway.utils.png_to_wall_runs import (
    matrix_to_wall_runs_payload,
    png_to_matrix,
    rgb_to_value,
    save_wall_runs_json,
    wall_runs_payload_to_matrix,
)


def test_rgb_to_value_exact_colors() -> None:
    assert rgb_to_value((255, 255, 255)) == 0
    assert rgb_to_value((255, 0, 0)) == 1
    assert rgb_to_value((0, 0, 255)) == 2


def test_rgb_to_value_nearest_color() -> None:
    assert rgb_to_value((250, 10, 10)) == 1
    assert rgb_to_value((5, 5, 245)) == 2
    assert rgb_to_value((240, 240, 240)) == 0


def test_rgb_to_value_strict_raises_on_unknown() -> None:
    with pytest.raises(ValueError):
        rgb_to_value((254, 10, 10), strict=True)


def test_png_to_matrix_and_wall_runs_export(tmp_path) -> None:
    image_path = tmp_path / "sample.png"
    output_path = tmp_path / "wall-runs.json"

    image = Image.new("RGB", (3, 2))
    image.putdata(
        [
            (255, 255, 255),
            (255, 0, 0),
            (0, 0, 255),
            (250, 0, 0),
            (0, 0, 250),
            (245, 245, 245),
        ]
    )
    image.save(image_path)

    matrix = png_to_matrix(image_path)
    assert matrix == [
        [0, 1, 2],
        [1, 2, 0],
    ]

    save_wall_runs_json(matrix, output_path, pretty=True)
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["encoding"] == "wall-runs-rb-v1"
    assert wall_runs_payload_to_matrix(payload) == matrix


def test_wall_runs_payload_roundtrip() -> None:
    matrix = [
        [0, 1, 1, 0, 2, 2, 2],
        [1, 1, 0, 0, 2, 0, 2],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    payload = matrix_to_wall_runs_payload(matrix)
    assert payload["encoding"] == "wall-runs-rb-v1"
    assert wall_runs_payload_to_matrix(payload) == matrix
