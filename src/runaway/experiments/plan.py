from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScenarioDefinition:
    name: str
    agents: int
    steps: int
    preset: str


DEFAULT_SEEDS = (7, 11, 19, 23, 31)

SCENARIO_MATRIX = (
    ScenarioDefinition(name="light-load", agents=80, steps=250, preset="small"),
    ScenarioDefinition(name="medium-load", agents=180, steps=320, preset="small"),
    ScenarioDefinition(name="heavy-load", agents=320, steps=420, preset="small"),
)
