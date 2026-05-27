from __future__ import annotations

import os
from typing import ClassVar

from mesa.visualization.modules import TextElement


class StatsDashboard(TextElement):
    """Real-time statistics panel rendered in the left sidebar."""

    package_includes: ClassVar = []
    local_includes: ClassVar = ["SidebarTextModule.js"]
    local_dir: ClassVar = os.path.join(os.path.dirname(__file__), "js")
    js_code = "elements.push(new SidebarTextModule());"

    def render(self, model) -> str:
        records = model.metrics.get_agent_records()
        if records:
            times = [r["steps_taken"] for r in records]
            avg_time_str = str(round(sum(times) / len(times), 1))
        else:
            avg_time_str = "\u2014"

        progress = (
            f"{round(model.evacuated_count / model.initial_agents * 100, 1)}%"
            if model.initial_agents > 0
            else "0%"
        )

        tiles = [
            ("\U0001f465", "Total", str(model.initial_agents), "#f1f5f9"),
            ("\u2705", "Evacuated", str(model.evacuated_count), "#dcfce7"),
            ("\U0001f3c3", "Remaining", str(model.active_agents), "#fee2e2"),
            ("\U0001f4ca", "Progress", progress, "#dbeafe"),
            ("\u23f1\ufe0f", "Step", str(model.step_count), "#f1f5f9"),
            ("\u23f3", "Avg Time", avg_time_str, "#fef9c3"),
        ]

        tiles_html = ""
        for icon, label, value, bg in tiles:
            tiles_html += (
                f'<div style="display:flex;flex-direction:column;align-items:center;'
                f"justify-content:center;background:{bg};padding:10px 6px;"
                f'border-radius:8px">'
                f'<div style="font-size:18px">{icon}</div>'
                f'<div style="font-size:21px;font-weight:700;color:#1e293b">'
                f"{value}</div>"
                f'<div style="font-size:10px;color:#64748b;text-transform:uppercase;'
                f'letter-spacing:0.3px">{label}</div>'
                f"</div>"
            )

        return (
            f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px">'
            f"{tiles_html}</div>"
        )
