from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from runaway.core.config import SimulationConfig
    from runaway.statistics.collector import MetricsCollector


@runtime_checkable
class ResultsWriter(Protocol):
    """Interface for writing simulation results to persistent storage."""

    def save(self, run_id: str, config: SimulationConfig, collector: MetricsCollector) -> None: ...
