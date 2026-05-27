"""Runaway package for building evacuation simulations."""

__all__ = ["EvacuationModel", "SimulationConfig"]


def __getattr__(name: str):
    if name == "SimulationConfig":
        from runaway.core.config import SimulationConfig

        return SimulationConfig
    if name == "EvacuationModel":
        from runaway.core.model import EvacuationModel

        return EvacuationModel
    raise AttributeError(f"module 'runaway' has no attribute {name!r}")
