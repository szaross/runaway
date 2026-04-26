import sys
from pathlib import Path

import pytest

from runaway import cli
from runaway.cli import _adaptive_visualization_grid


def test_adaptive_visualization_grid_is_dense_but_safe() -> None:
    width, height = _adaptive_visualization_grid()
    assert width >= 320
    assert height >= 181
    assert abs(height - round(453 * width / 800)) <= 1
    assert width * height <= 70_000


def test_cli_rejects_only_width() -> None:
    old_argv = sys.argv
    sys.argv = ["runaway", "--width", "800"]
    try:
        with pytest.raises(SystemExit) as exc:
            cli.main()
        assert exc.value.code == 2
    finally:
        sys.argv = old_argv


def test_cli_rejects_only_height() -> None:
    old_argv = sys.argv
    sys.argv = ["runaway", "--height", "453"]
    try:
        with pytest.raises(SystemExit) as exc:
            cli.main()
        assert exc.value.code == 2
    finally:
        sys.argv = old_argv


@pytest.mark.parametrize("suffix", [".json", ".csv"])
def test_cli_exports_history_file(tmp_path: Path, suffix: str) -> None:
    old_argv = sys.argv
    history_path = tmp_path / f"history{suffix}"
    sys.argv = [
        "runaway",
        "--preset",
        "small",
        "--steps",
        "2",
        "--agents",
        "20",
        "--seed",
        "4",
        "--history-out",
        str(history_path),
    ]
    try:
        cli.main()
    finally:
        sys.argv = old_argv

    assert history_path.is_file()
    content = history_path.read_text(encoding="utf-8")
    assert content.strip()


def test_cli_exports_summary_json(tmp_path: Path) -> None:
    old_argv = sys.argv
    summary_path = tmp_path / "summary.json"
    sys.argv = [
        "runaway",
        "--preset",
        "small",
        "--steps",
        "2",
        "--agents",
        "20",
        "--seed",
        "4",
        "--summary-out",
        str(summary_path),
    ]
    try:
        cli.main()
    finally:
        sys.argv = old_argv

    assert summary_path.is_file()
    payload = summary_path.read_text(encoding="utf-8")
    assert "evacuation_ratio" in payload


def test_cli_rejects_non_positive_floors() -> None:
    old_argv = sys.argv
    sys.argv = ["runaway", "--floors", "0"]
    try:
        with pytest.raises(SystemExit) as exc:
            cli.main()
        assert exc.value.code == 2
    finally:
        sys.argv = old_argv
