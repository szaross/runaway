from __future__ import annotations

import os
from importlib import import_module

import mesa

from runaway.core.agents import EvacueeAgent, ExitCell, StairCell, WallCell
from runaway.core.config import SimulationConfig
from runaway.core.model import EvacuationModel
from runaway.statistics.charts import create_evacuation_charts
from runaway.statistics.dashboard import StatsDashboard

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


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
        snapshot = agent.model.latest_snapshot

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

        if isinstance(agent, StairCell):
            return {
                "Shape": "rect",
                "Color": "#f59e0b",
                "Filled": "true",
                "Layer": 1,
                "w": 1,
                "h": 1,
            }

        if isinstance(agent, EvacueeAgent):
            floor = agent.position[0] if agent.position is not None else 0
            transfer_nodes = snapshot.transfer_nodes.get(floor, set())
            is_on_transfer = (
                agent.position is not None
                and (agent.position[1], agent.position[2]) in transfer_nodes
            )
            return {
                "Shape": "circle",
                "Color": "#7c3aed" if is_on_transfer else "#2563eb",
                "Filled": "true",
                "Layer": 2,
                "r": 0.7,
            }

        return {}

    # Canvas pixel size: ensure ~3px per cell for visibility.
    # For multi-floor the canvas is tall but floor-switching JS zooms into one floor.
    canvas_w = min(config.width * 3, 2400)
    canvas_h = min(config.height * config.floors_count * 3, config.floors_count * 1050)

    grid = CanvasGrid(
        portrayal,
        config.width,
        config.height * config.floors_count,
        canvas_w,
        canvas_h,
    )

    model_params = {
        "config": SimulationConfig(
            width=config.width,
            height=config.height,
            n_agents=config.n_agents,
            max_steps=config.max_steps,
            seed=config.seed,
            floors_count=config.floors_count,
            vertical_links_mode=config.vertical_links_mode,
            stair_traversal_cost=config.stair_traversal_cost,
        )
    }

    stats_dashboard = StatsDashboard()
    charts = create_evacuation_charts()

    server = ModularServer(
        EvacuationModel,
        [stats_dashboard, grid, *charts],
        "Runaway Evacuation",
        model_params,
    )
    server.port = port

    # Inject floors_count as a global JS variable for the floor switcher
    server.js_code = [f"window.__FLOORS_COUNT = {config.floors_count};"] + server.js_code

    # Override template path to use our custom 40/60 layout
    server.settings["template_path"] = _TEMPLATES_DIR

    server.launch()
