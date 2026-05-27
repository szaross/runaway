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
            ("Total", str(model.initial_agents), "#f1f5f9"),
            ("Evacuated", str(model.evacuated_count), "#dcfce7"),
            ("Remaining", str(model.active_agents), "#fee2e2"),
            ("Progress", progress, "#dbeafe"),
            ("Step", str(model.step_count), "#f1f5f9"),
            ("Avg Time", avg_time_str, "#fef9c3"),
        ]

        tiles_html = ""
        for label, value, bg in tiles:
            tiles_html += (
                f'<div style="display:flex;flex-direction:column;align-items:center;'
                f"justify-content:center;background:{bg};padding:10px 6px;"
                f'border-radius:8px">'
                f'<div style="font-size:21px;font-weight:700;color:#1e293b">'
                f"{value}</div>"
                f'<div style="font-size:10px;color:#64748b;text-transform:uppercase;'
                f'letter-spacing:0.3px">{label}</div>'
                f"</div>"
            )

        # Per-floor stats
        floors_html = ""
        if model.config.floors_count > 1:
            floors_html = (
                '<div style="margin-top:10px;display:flex;flex-direction:column;gap:4px">'
            )
            for floor in range(model.config.floors_count):
                # Count agents still on this floor
                remaining_on_floor = sum(
                    1
                    for a in model._active_agents
                    if a.position is not None and a.position[0] == floor
                )
                # Count agents that started on this floor
                started_on_floor = sum(
                    1
                    for a in model._active_agents
                    if a.start_floor == floor
                ) + sum(
                    1
                    for r in records
                    if r.get("start_floor") == floor
                )
                evacuated_from_floor = started_on_floor - sum(
                    1
                    for a in model._active_agents
                    if a.start_floor == floor
                )
                if started_on_floor > 0:
                    pct = round(evacuated_from_floor / started_on_floor * 100, 1)
                else:
                    pct = 0.0
                floors_html += (
                    f'<div style="display:flex;align-items:center;justify-content:space-between;'
                    f'background:#f8fafc;padding:6px 10px;border-radius:6px;font-size:11px">'
                    f'<span style="font-weight:600;color:#334155">'
                    f'Floor {floor + 1}</span>'
                    f'<span style="color:#475569">'
                    f'{evacuated_from_floor}/{started_on_floor}'
                    f' \u2014 {pct}%</span>'
                    f"</div>"
                )
            floors_html += "</div>"

        return (
            f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px">'
            f"{tiles_html}</div>{floors_html}"
        )
