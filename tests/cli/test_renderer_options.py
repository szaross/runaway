import sys
import types

import pytest

from runaway import cli


def test_cli_uses_pygame_renderer_when_requested(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    fake_mod = types.ModuleType("runaway.pygame_visualization")
    fake_mod.launch_pygame = lambda config: calls.append(f"{config.width}x{config.height}")
    monkeypatch.setitem(sys.modules, "runaway.pygame_visualization", fake_mod)

    old_argv = sys.argv
    sys.argv = ["runaway", "--renderer", "pygame", "--preset", "small", "--steps", "1"]
    try:
        cli.main()
    finally:
        sys.argv = old_argv

    assert calls == ["320x181"]


def test_cli_visualize_flag_routes_to_mesa(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []
    fake_mod = types.ModuleType("runaway.visualization")
    fake_mod.launch_server = lambda config, port: calls.append(port)
    monkeypatch.setitem(sys.modules, "runaway.visualization", fake_mod)

    old_argv = sys.argv
    sys.argv = ["runaway", "--visualize", "--port", "9001"]
    try:
        cli.main()
    finally:
        sys.argv = old_argv

    assert calls == [9001]


def test_cli_rejects_visualize_combined_with_pygame() -> None:
    old_argv = sys.argv
    sys.argv = ["runaway", "--visualize", "--renderer", "pygame"]
    try:
        with pytest.raises(SystemExit) as exc:
            cli.main()
        assert exc.value.code == 2
    finally:
        sys.argv = old_argv
