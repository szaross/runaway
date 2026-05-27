from runaway.core.config import SimulationConfig
from runaway.core.model import EvacuationModel


def test_model_run_keeps_agent_accounting_consistent() -> None:
    config = SimulationConfig(width=800, height=453, n_agents=220, max_steps=140, seed=7)
    model = EvacuationModel(config)

    model.run()

    assert model.step_count <= config.max_steps
    assert model.evacuated_count + model.active_agents == model.initial_agents
    assert len(model.history) >= 1


def test_occupancy_matches_active_agents_each_step() -> None:
    config = SimulationConfig(width=800, height=453, n_agents=160, max_steps=60, seed=11)
    model = EvacuationModel(config)

    for _ in range(20):
        model.step()
        assert len(model.occupied_cells) == model.active_agents


def test_grid_position_matches_agent_position() -> None:
    config = SimulationConfig(width=800, height=453, n_agents=120, max_steps=30, seed=5)
    model = EvacuationModel(config)

    model.step()

    for agent in model._active_agents:
        assert agent.position is not None
        assert agent.pos == model.to_grid_pos(agent.position)


def test_multifloor_uses_vertical_links() -> None:
    config = SimulationConfig(
        width=320,
        height=181,
        n_agents=80,
        max_steps=5,
        seed=13,
        floors_count=2,
    )
    model = EvacuationModel(config)

    assert model.transfer_links
    assert any(link.source[0] != link.target[0] for link in model.transfer_links)


def test_snapshot_exposes_floor_aware_state() -> None:
    config = SimulationConfig(
        width=320, height=181, n_agents=30, max_steps=5, seed=2, floors_count=2
    )
    model = EvacuationModel(config)
    snap = model.snapshot()

    assert snap.floors_count == 2
    assert len(snap.walls) == 2
    assert len(snap.exits) == 2
    assert len(snap.transfer_nodes) == 2
