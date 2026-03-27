import sys

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
