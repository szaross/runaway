from runaway.core.model import AgentSnapshot, SimulationSnapshot
from runaway.renderers.pygame import frame_for_floor


def _sample_snapshot() -> SimulationSnapshot:
    return SimulationSnapshot(
        step=3,
        evacuated=1,
        remaining=2,
        floors_count=2,
        walls={0: {(0, 0)}, 1: {(1, 1)}},
        exits={0: {(2, 2)}, 1: {(3, 3)}},
        transfer_nodes={0: {(4, 4)}, 1: {(5, 5)}},
        agents=[
            AgentSnapshot(unique_id=1, position=(0, 10, 10), evacuated=False),
            AgentSnapshot(unique_id=2, position=(1, 20, 20), evacuated=False),
        ],
    )


def test_frame_for_floor_filters_entities_for_selected_floor() -> None:
    frame = frame_for_floor(_sample_snapshot(), active_floor=1)

    assert frame.floor == 1
    assert frame.walls == {(1, 1)}
    assert frame.exits == {(3, 3)}
    assert frame.transfer_nodes == {(5, 5)}
    assert [agent.unique_id for agent in frame.agents] == [2]


def test_frame_for_floor_clamps_out_of_range_floor_index() -> None:
    low = frame_for_floor(_sample_snapshot(), active_floor=-20)
    high = frame_for_floor(_sample_snapshot(), active_floor=99)

    assert low.floor == 0
    assert high.floor == 1
