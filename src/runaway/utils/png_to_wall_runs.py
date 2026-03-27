from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

COLOR_TO_VALUE = {
    WHITE: 0,
    RED: 1,
    BLUE: 2,
}


def _distance_sq(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


def rgb_to_value(pixel: tuple[int, int, int], *, strict: bool = False) -> int:
    if pixel in COLOR_TO_VALUE:
        return COLOR_TO_VALUE[pixel]
    if strict:
        allowed = ", ".join(str(color) for color in COLOR_TO_VALUE)
        raise ValueError(f"Unexpected color {pixel}. Allowed colors: {allowed}")

    nearest_color = min(COLOR_TO_VALUE, key=lambda color: _distance_sq(pixel, color))
    return COLOR_TO_VALUE[nearest_color]


def png_to_matrix(image_path: str | Path, *, strict: bool = False) -> list[list[int]]:
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError(
            "png_to_matrix requires Pillow. Install it with: pip install 'runaway[png]'"
        ) from exc
    with Image.open(image_path) as image:
        image = image.convert("RGB")
        width, height = image.size
        pixels = image.load()
        matrix: list[list[int]] = []

        for y in range(height):
            row: list[int] = []
            for x in range(width):
                row.append(rgb_to_value(pixels[x, y], strict=strict))
            matrix.append(row)

    return matrix


def _row_runs(row: list[int], target: int, y: int) -> list[list[int]]:
    runs: list[list[int]] = []
    start: int | None = None
    for x, value in enumerate(row):
        if value == target and start is None:
            start = x
        elif value != target and start is not None:
            runs.append([y, start, x - 1])
            start = None
    if start is not None:
        runs.append([y, start, len(row) - 1])
    return runs


def matrix_to_wall_runs_payload(matrix: list[list[int]]) -> dict[str, Any]:
    height = len(matrix)
    width = len(matrix[0]) if matrix else 0
    red_runs: list[list[int]] = []
    blue_runs: list[list[int]] = []

    for y, row in enumerate(matrix):
        red_runs.extend(_row_runs(row, 1, y))
        blue_runs.extend(_row_runs(row, 2, y))

    return {
        "width": width,
        "height": height,
        "encoding": "wall-runs-rb-v1",
        "values": {"white": 0, "red": 1, "blue": 2},
        "red_runs": red_runs,
        "blue_runs": blue_runs,
    }


def wall_runs_payload_to_matrix(payload: dict[str, Any]) -> list[list[int]]:
    width = int(payload["width"])
    height = int(payload["height"])
    matrix = [[0 for _ in range(width)] for _ in range(height)]

    for y, x_start, x_end in payload.get("red_runs", []):
        for x in range(x_start, x_end + 1):
            matrix[y][x] = 1
    for y, x_start, x_end in payload.get("blue_runs", []):
        for x in range(x_start, x_end + 1):
            matrix[y][x] = 2
    return matrix


def save_wall_runs_json(
    matrix: list[list[int]],
    output_path: str | Path,
    *,
    pretty: bool = False,
) -> None:
    payload = matrix_to_wall_runs_payload(matrix)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2 if pretty else None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert a PNG floor plan into wall-runs JSON.")
    parser.add_argument("--input", required=True, help="Input PNG path")
    parser.add_argument("--output", required=True, help="Output JSON path (wall-runs-rb-v1)")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when any pixel is not exactly white/red/blue",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    matrix = png_to_matrix(args.input, strict=args.strict)
    save_wall_runs_json(matrix, args.output, pretty=args.pretty)
    height = len(matrix)
    width = len(matrix[0]) if matrix else 0
    print(f"Saved wall-runs from {height}x{width} PNG to {args.output}")


if __name__ == "__main__":
    main()
