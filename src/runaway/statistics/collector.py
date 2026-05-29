from __future__ import annotations

from statistics import median
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from runaway.core.agents import EvacueeAgent


class MetricsCollector:
    """Collects per-step and per-agent evacuation metrics. Has no I/O responsibilities."""

    def __init__(self) -> None:
        self._step_history: list[dict[str, Any]] = []
        self._agent_records: list[dict[str, Any]] = []

    def on_step(self, model: Any) -> None:
        """Record metrics for the current simulation step."""
        evacuated = model.evacuated_count
        remaining = model.active_agents
        total = model.initial_agents
        evacuation_pct = (evacuated / total * 100) if total > 0 else 0.0

        record: dict[str, Any] = {
            "step": model.step_count,
            "evacuated": evacuated,
            "remaining": remaining,
            "evacuation_pct": round(evacuation_pct, 2),
        }

        # Per-floor remaining counts
        floor_counts: dict[int, int] = {}
        for agent in model._active_agents:
            if agent.position is not None:
                floor = agent.position[0]
                floor_counts[floor] = floor_counts.get(floor, 0) + 1

        for floor in range(model.config.floors_count):
            record[f"floor{floor}_remaining"] = floor_counts.get(floor, 0)

        self._step_history.append(record)

    def on_agent_evacuated(self, agent: EvacueeAgent, step: int) -> None:
        """Record an agent's evacuation event."""
        self._agent_records.append(
            {
                "agent_id": agent.unique_id,
                "start_floor": agent.start_floor,
                "evacuation_step": step,
                "steps_taken": agent.steps_taken,
            }
        )

    def get_summary(self) -> dict[str, Any]:
        """Return aggregate statistics for the simulation run."""
        last = self._step_history[-1] if self._step_history else {}
        total_steps = last.get("step", 0)
        evacuated = last.get("evacuated", 0)
        remaining = last.get("remaining", 0)
        total = evacuated + remaining
        ratio = (evacuated / total) if total > 0 else 0.0

        evac_times = [r["steps_taken"] for r in self._agent_records]

        summary: dict[str, Any] = {
            "total_steps": total_steps,
            "evacuated": evacuated,
            "remaining": remaining,
            "evacuation_ratio": round(ratio, 4),
            "avg_evacuation_time": (
                round(sum(evac_times) / len(evac_times), 2) if evac_times else None
            ),
            "min_evacuation_time": min(evac_times) if evac_times else None,
            "max_evacuation_time": max(evac_times) if evac_times else None,
            "median_evacuation_time": round(median(evac_times), 2) if evac_times else None,
        }
        return summary

    def get_step_history(self) -> list[dict[str, Any]]:
        """Return the full list of per-step metric records."""
        return list(self._step_history)

    def get_agent_records(self) -> list[dict[str, Any]]:
        """Return the full list of per-agent evacuation records."""
        return list(self._agent_records)
