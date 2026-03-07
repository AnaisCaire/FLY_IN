"""Pygame visualizer for the Fly-in drone simulation."""

import sys
import pygame
from typing import Dict, List, Tuple, Set
from src.models import Manager, ZoneType

COLORS = {
    "bg": (20, 20, 20),
    "connection": (80, 80, 80),
    "normal": (70, 130, 180),
    "restricted": (200, 50, 50),
    "priority": (50, 160, 80),
    "start": (100, 220, 100),
    "end": (220, 100, 100),
    "drone": (255, 220, 0),
    "drone_text": (0, 0, 0),
    "zone_text": (200, 200, 200),
    "cap_text": (140, 140, 140),
    "white": (255, 255, 255),
}

TURN_DURATION_MS = 500
MAX_VISIBLE_DRONES = 6


class Visualizer:
    def __init__(
        self,
        manager: Manager,
        snapshots: List[Dict[str, str]],
    ) -> None:
        self.manager = manager
        self.snapshots = snapshots

        pygame.init()

        xs = [z.x for z in manager.zone.values()]
        ys = [z.y for z in manager.zone.values()]
        self.min_x, self.max_x = min(xs), max(xs)
        self.min_y, self.max_y = min(ys), max(ys)

        range_x = max(self.max_x - self.min_x, 1)
        range_y = max(self.max_y - self.min_y, 1)

        hud_h = 80
        pad = 80

        max_w, max_h = 1600, 900
        usable_w = max_w - 2 * pad
        usable_h = max_h - hud_h - 2 * pad

        scale_x = usable_w // range_x
        scale_y = usable_h // range_y
        self.scale = max(min(scale_x, scale_y, 110), 40)

        self.zone_r = max(10, min(18, self.scale // 4))
        self.drone_r = max(5, self.zone_r // 2)
        self.drone_sp = self.drone_r * 2 + 4

        graph_w = range_x * self.scale
        graph_h = range_y * self.scale

        win_w = max(graph_w + 2 * pad, 900)
        win_h = max(graph_h + hud_h + 2 * pad + 60, 600)

        self.offset_x = (
            (win_w - graph_w) // 2 - self.min_x * self.scale
        )
        self.offset_y = (
            hud_h
            + pad
            + (win_h - hud_h - 2 * pad - graph_h) // 2
            - self.min_y * self.scale
        )

        self.screen = pygame.display.set_mode((win_w, win_h))
        pygame.display.set_caption("Fly-in Drone Simulator")
        self.clock = pygame.time.Clock()
        font_size = max(9, self.scale // 8)
        self.font = pygame.font.SysFont("Arial", font_size)
        self.font_title = pygame.font.SysFont("Arial", 16, bold=True)

    def _to_screen(self, x: int, y: int) -> Tuple[int, int]:
        return (
            int(x * self.scale + self.offset_x),
            int(y * self.scale + self.offset_y),
        )

    def _zone_color(self, zone_name: str) -> Tuple[int, int, int]:
        zone = self.manager.zone.get(zone_name)
        if zone is None:
            return COLORS["normal"]
        if zone.is_start:
            return COLORS["start"]
        if zone.is_end:
            return COLORS["end"]
        if zone.zone_type == ZoneType.RESTRICTED:
            return COLORS["restricted"]
        if zone.zone_type == ZoneType.PRIORITY:
            return COLORS["priority"]
        return COLORS["normal"]

    def _draw_connections(self) -> None:
        drawn: Set[Tuple[str, str]] = set()
        for connections in self.manager.adjacency_list.values():
            for conn in connections:
                a, b = tuple(
                    sorted([conn.prev_zone.name, conn.next_zone.name])
                )
                key: Tuple[str, str] = (a, b)
                if key in drawn:
                    continue
                drawn.add(key)
                s = self._to_screen(conn.prev_zone.x, conn.prev_zone.y)
                e = self._to_screen(conn.next_zone.x, conn.next_zone.y)
                pygame.draw.line(self.screen, COLORS["connection"], s, e, 2)
                if conn.max_link_capacity > 1:
                    mid = ((s[0] + e[0]) // 2, (s[1] + e[1]) // 2)
                    lbl = self.font.render(
                        f"x{conn.max_link_capacity}", True, (120, 120, 120)
                    )
                    self.screen.blit(lbl, (mid[0] + 3, mid[1] - 8))

    def _draw_zones(self) -> None:
        for zone in self.manager.zone.values():
            pos = self._to_screen(zone.x, zone.y)
            color = self._zone_color(zone.name)
            pygame.draw.circle(self.screen, color, pos, self.zone_r)
            pygame.draw.circle(
                self.screen, COLORS["white"], pos, self.zone_r, 2
            )
            name_lbl = self.font.render(zone.name, True, COLORS["zone_text"])
            self.screen.blit(
                name_lbl,
                (pos[0] - name_lbl.get_width() // 2, pos[1] + self.zone_r + 3),
            )
            if not (zone.is_start or zone.is_end):
                cap_lbl = self.font.render(
                    f"cap {zone.max_drones}", True, COLORS["cap_text"]
                )
                self.screen.blit(
                    cap_lbl,
                    (
                        pos[0] - cap_lbl.get_width() // 2,
                        pos[1] + self.zone_r + 14,
                    ),
                )

    def _draw_drones(self, snapshot: Dict[str, str]) -> None:
        zone_drones: Dict[str, List[str]] = {}
        for label, zone_name in snapshot.items():
            zone_drones.setdefault(zone_name, []).append(label)

        for zone_name, labels in zone_drones.items():
            zone = self.manager.zone.get(zone_name)
            if zone is None:
                continue
            cx, cy = self._to_screen(zone.x, zone.y)
            visible = sorted(labels)[:MAX_VISIBLE_DRONES]
            n = len(visible)

            for i, label in enumerate(visible):
                dx = int((i - (n - 1) / 2) * self.drone_sp)
                px = cx + dx
                py = cy - self.zone_r - self.drone_r - 4
                pygame.draw.circle(
                    self.screen, COLORS["drone"], (px, py), self.drone_r
                )
                pygame.draw.circle(
                    self.screen, COLORS["white"], (px, py), self.drone_r, 1
                )
                id_lbl = self.font.render(label, True, COLORS["drone_text"])
                self.screen.blit(
                    id_lbl,
                    (px - id_lbl.get_width() // 2,
                     py - id_lbl.get_height() // 2),
                )

            extra = len(labels) - MAX_VISIBLE_DRONES
            if extra > 0:
                last_dx = int(((n - 1) - (n - 1) / 2) * self.drone_sp)
                ex_lbl = self.font.render(f"+{extra}", True, COLORS["drone"])
                self.screen.blit(
                    ex_lbl,
                    (
                        cx + last_dx + self.drone_r + 4,
                        cy - self.zone_r - self.drone_r * 2,
                    ),
                )

    def _draw_hud(self, turn: int, total: int) -> None:
        title = self.font_title.render(
            f"Fly-in Simulation  -  Turn {turn} / {total}  "
            f"({'DONE' if turn == total else 'running...'})",
            True, COLORS["white"],
        )
        self.screen.blit(title, (16, 10))
        legend = [
            ("Start", COLORS["start"]),
            ("End", COLORS["end"]),
            ("Normal", COLORS["normal"]),
            ("Restricted", COLORS["restricted"]),
            ("Priority", COLORS["priority"]),
        ]
        lx = 16
        for name, color in legend:
            pygame.draw.circle(self.screen, color, (lx + 6, 50), 6)
            lbl = self.font.render(name, True, COLORS["zone_text"])
            self.screen.blit(lbl, (lx + 16, 43))
            lx += lbl.get_width() + 28

    def run(self) -> None:
        total = len(self.snapshots)
        current_turn = 0
        last_advance = pygame.time.get_ticks()
        running = True
        while running:
            now = pygame.time.get_ticks()
            if (
                now - last_advance >= TURN_DURATION_MS
                and current_turn < total - 1
            ):
                current_turn += 1
                last_advance = now
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if (
                        event.key == pygame.K_RIGHT
                        and current_turn < total - 1
                    ):
                        current_turn += 1
                        last_advance = now
                    if (
                        event.key == pygame.K_LEFT
                        and current_turn > 0
                    ):
                        current_turn -= 1
                        last_advance = now
            self.screen.fill(COLORS["bg"])
            self._draw_connections()
            self._draw_zones()
            self._draw_drones(self.snapshots[current_turn])
            self._draw_hud(current_turn + 1, total)
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()


def main() -> None:
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: python3 src/visualizer.py <map_file>\n")
        sys.exit(1)
    from src.parser import Parser
    from src.engine import EngineSimulation
    from src.exceptions import FlyInError
    try:
        parser = Parser(sys.argv[1])
        parser.parsing()
        manager = parser.manager
    except (FlyInError, FileNotFoundError) as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
    try:
        engine = EngineSimulation(manager)
        _, snapshots = engine.run_with_snapshots()
    except FlyInError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
    Visualizer(manager, snapshots).run()


if __name__ == "__main__":
    main()
