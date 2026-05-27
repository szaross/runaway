from __future__ import annotations

import csv
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from runaway.core.config import SimulationConfig
    from runaway.statistics.collector import MetricsCollector


class CsvResultsWriter:
    """Writes simulation results to CSV files. Single responsibility: file I/O only."""

    MIN_STEPS_TO_SAVE = 5

    def __init__(self, output_dir: str = "results") -> None:
        self._output_dir = output_dir

    def save(self, run_id: str, config: SimulationConfig, collector: MetricsCollector) -> None:
        if len(collector.get_step_history()) < self.MIN_STEPS_TO_SAVE:
            return

        sim_dir = os.path.join(self._output_dir, f"sim_{run_id.replace(':', '-')}")
        os.makedirs(sim_dir, exist_ok=True)

        self._save_runs(sim_dir, run_id, config, collector)
        self._save_agent_events(sim_dir, collector)
        self._save_step_history(sim_dir, config, collector)

    def _save_runs(
        self, sim_dir: str, run_id: str, config: SimulationConfig, collector: MetricsCollector
    ) -> None:
        summary = collector.get_summary()
        path = os.path.join(sim_dir, "runs.csv")

        fieldnames = [
            "run_id",
            "scenario",
            "seed",
            "floors",
            "n_agents",
            "total_steps",
            "evacuated",
            "remaining",
            "evacuation_ratio",
            "avg_evacuation_time",
            "min_evacuation_time",
            "max_evacuation_time",
            "median_evacuation_time",
        ]

        row = {
            "run_id": run_id,
            "scenario": getattr(config, "scenario", None) or "",
            "seed": config.seed,
            "floors": config.floors_count,
            "n_agents": config.n_agents,
            "total_steps": summary["total_steps"],
            "evacuated": summary["evacuated"],
            "remaining": summary["remaining"],
            "evacuation_ratio": summary["evacuation_ratio"],
            "avg_evacuation_time": summary["avg_evacuation_time"],
            "min_evacuation_time": summary["min_evacuation_time"],
            "max_evacuation_time": summary["max_evacuation_time"],
            "median_evacuation_time": summary["median_evacuation_time"],
        }

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(row)

    def _save_agent_events(self, sim_dir: str, collector: MetricsCollector) -> None:
        path = os.path.join(sim_dir, "agent_events.csv")

        fieldnames = ["agent_id", "start_floor", "evacuation_step", "steps_taken"]

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for record in collector.get_agent_records():
                writer.writerow(record)

    def _save_step_history(
        self, sim_dir: str, config: SimulationConfig, collector: MetricsCollector
    ) -> None:
        path = os.path.join(sim_dir, "step_history.csv")

        floor_columns = [f"floor{i}_remaining" for i in range(config.floors_count)]
        fieldnames = ["step", "evacuated", "remaining", "evacuation_pct"] + floor_columns

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for record in collector.get_step_history():
                writer.writerow(record)
