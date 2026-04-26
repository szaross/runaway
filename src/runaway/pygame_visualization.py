from __future__ import annotations

from dataclasses import dataclass

from runaway.config import SimulationConfig
from runaway.model import AgentSnapshot, EvacuationModel, SimulationSnapshot

_COLOR_BG = (249, 250, 251)
_COLOR_GRID = (229, 231, 235)
_COLOR_WALL = (31, 41, 55)
_COLOR_EXIT = (22, 163, 74)
_COLOR_TRANSFER = (234, 179, 8)
_COLOR_AGENT = (37, 99, 235)
_COLOR_TEXT = (17, 24, 39)
_COLOR_LABEL_BG = (255, 255, 255)
_COLOR_LABEL_BORDER = (156, 163, 175)


@dataclass(frozen=True, slots=True)
class FloorFrame:
    floor: int
    walls: set[tuple[int, int]]
    exits: set[tuple[int, int]]
    transfer_nodes: set[tuple[int, int]]
    agents: list[AgentSnapshot]


def frame_for_floor(snapshot: SimulationSnapshot, *, active_floor: int) -> FloorFrame:
    floor = max(0, min(active_floor, snapshot.floors_count - 1))
    agents = [agent for agent in snapshot.agents if agent.position[0] == floor]
    return FloorFrame(
        floor=floor,
        walls=set(snapshot.walls.get(floor, set())),
        exits=set(snapshot.exits.get(floor, set())),
        transfer_nodes=set(snapshot.transfer_nodes.get(floor, set())),
        agents=agents,
    )


class PygameRendererAdapter:
    """Desktop pygame renderer that consumes SimulationSnapshot only."""

    def __init__(
        self,
        *,
        width: int,
        height: int,
        start_floor: int = 0,
        cell_px: int = 6,
        panel_px: int = 76,
        max_fps: int = 30,
    ) -> None:
        try:
            import pygame
        except Exception as exc:  # pragma: no cover - depends on optional dependency
            raise RuntimeError(
                "Renderer 'pygame' requires optional dependency 'pygame'. "
                "Install it with: pip install -U pygame"
            ) from exc

        self._pygame = pygame
        self._width = width
        self._height = height
        self._cell_px = max(2, cell_px)
        self._panel_px = max(40, panel_px)
        self._max_fps = max(1, max_fps)
        self._active_floor = max(0, start_floor)
        self._clock = pygame.time.Clock()

        pygame.init()
        pygame.display.set_caption("Runaway - pygame renderer")
        surface_w = self._width * self._cell_px
        surface_h = self._height * self._cell_px + self._panel_px
        self._surface = pygame.display.set_mode((surface_w, surface_h))
        self._font = pygame.font.SysFont("Arial", 18)

    @property
    def active_floor(self) -> int:
        return self._active_floor

    def process_events(self, *, floors_count: int) -> bool:
        pygame = self._pygame
        floor_max = max(0, floors_count - 1)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type != pygame.KEYDOWN:
                continue
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                return False
            if event.key in (pygame.K_UP, pygame.K_RIGHT, pygame.K_RIGHTBRACKET):
                self._active_floor = min(floor_max, self._active_floor + 1)
            if event.key in (pygame.K_DOWN, pygame.K_LEFT, pygame.K_LEFTBRACKET):
                self._active_floor = max(0, self._active_floor - 1)

        self._active_floor = max(0, min(self._active_floor, floor_max))
        return True

    def render(self, snapshot: SimulationSnapshot) -> None:
        pygame = self._pygame
        frame = frame_for_floor(snapshot, active_floor=self._active_floor)
        self._active_floor = frame.floor
        cell = self._cell_px

        self._surface.fill(_COLOR_BG)

        for x in range(self._width + 1):
            pygame.draw.line(
                self._surface,
                _COLOR_GRID,
                (x * cell, 0),
                (x * cell, self._height * cell),
                1,
            )
        for y in range(self._height + 1):
            pygame.draw.line(
                self._surface,
                _COLOR_GRID,
                (0, y * cell),
                (self._width * cell, y * cell),
                1,
            )

        for x, y in frame.walls:
            pygame.draw.rect(self._surface, _COLOR_WALL, (x * cell, y * cell, cell, cell))
        for x, y in frame.exits:
            pygame.draw.rect(self._surface, _COLOR_EXIT, (x * cell, y * cell, cell, cell))
        for x, y in frame.transfer_nodes:
            pad = max(1, cell // 4)
            pygame.draw.rect(
                self._surface,
                _COLOR_TRANSFER,
                (x * cell + pad, y * cell + pad, max(2, cell - 2 * pad), max(2, cell - 2 * pad)),
            )

        agent_radius = max(2, cell // 2)
        for agent in frame.agents:
            _, ax, ay = agent.position
            pygame.draw.circle(
                self._surface,
                _COLOR_AGENT,
                (ax * cell + cell // 2, ay * cell + cell // 2),
                agent_radius,
            )

        floor_label = f"Floor {frame.floor + 1}/{snapshot.floors_count}"
        floor_label_surface = self._font.render(floor_label, True, _COLOR_TEXT)
        floor_label_rect = floor_label_surface.get_rect(topleft=(10, 10))
        floor_bg_rect = floor_label_rect.inflate(12, 8)
        pygame.draw.rect(self._surface, _COLOR_LABEL_BG, floor_bg_rect, border_radius=6)
        pygame.draw.rect(self._surface, _COLOR_LABEL_BORDER, floor_bg_rect, width=1, border_radius=6)
        self._surface.blit(floor_label_surface, floor_label_rect)

        panel_top = self._height * cell + 10
        status = (
            f"step={snapshot.step} evacuated={snapshot.evacuated} "
            f"remaining={snapshot.remaining} floor={frame.floor + 1}/{snapshot.floors_count}"
        )
        help_text = "keys: [ ] or arrows switch floor, q/esc quit"
        self._surface.blit(self._font.render(status, True, _COLOR_TEXT), (10, panel_top))
        self._surface.blit(self._font.render(help_text, True, _COLOR_TEXT), (10, panel_top + 28))
        pygame.display.flip()
        self._clock.tick(self._max_fps)

    def close(self) -> None:
        self._pygame.quit()


def launch_pygame(config: SimulationConfig) -> None:
    """Run simulation loop with pygame renderer."""
    model = EvacuationModel(config)
    renderer = PygameRendererAdapter(
        width=config.width,
        height=config.height,
        start_floor=0,
    )

    running = True
    try:
        renderer.render(model.latest_snapshot)
        while running and model.active_agents > 0 and model.step_count < config.max_steps:
            running = renderer.process_events(floors_count=config.floors_count)
            if not running:
                break
            model.step()
            renderer.render(model.latest_snapshot)
    finally:
        renderer.close()
