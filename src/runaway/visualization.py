from __future__ import annotations

from importlib import import_module

import mesa

from runaway.agents import EvacueeAgent, ExitCell, WallCell
from runaway.config import SimulationConfig
from runaway.model import EvacuationModel


def launch_server(config: SimulationConfig, *, port: int = 8521) -> None:
    """Launch Mesa browser visualization server."""
    try:
        mod_vis = import_module("mesa.visualization.ModularVisualization")
        mod_modules = import_module("mesa.visualization.modules")
        ModularServer = mod_vis.ModularServer
        CanvasGrid = mod_modules.CanvasGrid
    except Exception as exc:  # pragma: no cover - depends on optional viz deps
        mesa_version = getattr(mesa, "__version__", "unknown")
        raise RuntimeError(
            "Could not load legacy Mesa visualization API (ModularServer/CanvasGrid). "
            f"Detected mesa=={mesa_version}. "
            "Use a compatible version and extras: "
            'pip install -U "mesa[viz]>=2.2,<3.0"'
        ) from exc

    def portrayal(agent):
        if isinstance(agent, WallCell):
            return {
                "Shape": "rect",
                "Color": "#1f2937",
                "Filled": "true",
                "Layer": 0,
                "w": 1,
                "h": 1,
            }

        if isinstance(agent, ExitCell):
            return {
                "Shape": "rect",
                "Color": "#16a34a",
                "Filled": "true",
                "Layer": 1,
                "w": 1,
                "h": 1,
            }

        if isinstance(agent, EvacueeAgent):
            return {
                "Shape": "circle",
                "Color": "#2563eb",
                "Filled": "true",
                "Layer": 2,
                "r": 0.7,
            }

        return {}

    grid = CanvasGrid(
        portrayal,
        config.width,
        config.height,
        min(config.width * 3, 2400),
        min(config.height * 3, 1050),
    )

    model_params = {
        "config": SimulationConfig(
            width=config.width,
            height=config.height,
            n_agents=config.n_agents,
            max_steps=config.max_steps,
            seed=config.seed,
        )
    }

    server = ModularServer(
        EvacuationModel,
        [grid],
        "Runaway Evacuation",
        model_params,
    )
    server.port = port
    server.launch()
