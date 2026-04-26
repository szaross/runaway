from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any

from runaway.core.model import EvacuationModel


def compute_summary_metrics(model: EvacuationModel) -> dict[str, Any]:
    """Return stable aggregate metrics for reports and comparisons."""
    final_step = model.history[-1]["step"] if model.history else model.step_count
    remaining_series = [point["remaining"] for point in model.history]
    evacuated_series = [point["evacuated"] for point in model.history]
    total = max(model.initial_agents, 1)

    return {
        "steps_executed": model.step_count,
        "final_step": final_step,
        "initial_agents": model.initial_agents,
        "evacuated_agents": model.evacuated_count,
        "remaining_agents": model.active_agents,
        "evacuation_ratio": model.evacuated_count / total,
        "fully_evacuated": model.active_agents == 0,
        "peak_remaining": max(remaining_series, default=model.active_agents),
        "avg_remaining": mean(remaining_series) if remaining_series else float(model.active_agents),
        "peak_evacuated": max(evacuated_series, default=model.evacuated_count),
    }


def write_history_json(history: list[dict[str, int]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(history, indent=2), encoding="utf-8")


def write_history_csv(history: list[dict[str, int]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["step", "evacuated", "remaining"])
        writer.writeheader()
        for row in history:
            writer.writerow(row)


def write_summary_json(summary: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
