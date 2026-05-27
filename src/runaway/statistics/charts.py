from __future__ import annotations

import os
from typing import ClassVar

from mesa.visualization.ModularVisualization import VisualizationElement

_JS_DIR = os.path.join(os.path.dirname(__file__), "js")


class SidebarChart(VisualizationElement):
    """Chart module that renders into the sidebar panel."""

    package_includes: ClassVar = ["external/chart-3.6.1.min.js"]
    local_includes: ClassVar = ["SidebarChartModule.js"]
    local_dir: ClassVar = _JS_DIR

    def __init__(
        self,
        series: list[dict[str, str]],
        canvas_height: int = 200,
        canvas_width: int = 500,
        data_collector_name: str = "datacollector",
    ) -> None:
        super().__init__()
        self.series = series
        self.canvas_height = canvas_height
        self.canvas_width = canvas_width
        self.data_collector_name = data_collector_name

        series_json = str(series).replace("'", '"')
        self.js_code = (
            f"elements.push(new SidebarChartModule("
            f"{series_json}, {canvas_width}, {canvas_height}));"
        )

    def render(self, model) -> list:
        dc = getattr(model, self.data_collector_name)
        data = []
        for s in self.series:
            name = s["Label"]
            try:
                val = dc.model_vars[name][-1]
            except (KeyError, IndexError):
                val = 0
            data.append(val)
        return data


def create_evacuation_charts() -> list[SidebarChart]:
    """Create chart modules for the Mesa browser visualization."""
    return [
        SidebarChart(
            [
                {"Label": "Evacuated", "Color": "#16a34a"},
                {"Label": "Remaining", "Color": "#dc2626"},
            ],
            canvas_height=200,
            canvas_width=400,
            data_collector_name="datacollector",
        ),
    ]
