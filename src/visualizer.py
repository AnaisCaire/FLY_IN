"""Pygame visualizer for the Fly-in drone simulation."""

import sys
import pygame
from typing import Dict, List, Tuple
from src.models import Manager, ZoneType

# --- constants ---
BG = (20,  20,  20)
GREY = (80,  80,  80)
WHITE = (255, 255, 255)
YELLOW = (255, 220,   0)
BLACK = (0,   0,    0)
ZONE_COLORS = {
    "start":      (100, 220, 100),
    "end":        (220, 100, 100),
    "restricted": (200,  50,  50),
    "priority":   (50,  160,  80),
    "normal":     (70,  130, 180),
}
WIN_W, WIN_H = 1400, 800
PAD = 60
HUD_H = 70
MS_PER_TURN = 500


class Visualizer:
    def __init__(
        self,
        manager: Manager,
        snapshots: List[Dict[str, str]],
    ) -> None:
        self.manager = manager
        self.snapshots = snapshots

        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Fly-in")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 11)
        self.hfont = pygame.font.SysFont("Arial", 15, bold=True)

        # fit graph into usable area
        xs = [z.x for z in manager.zone.values()]
        ys = [z.y for z in manager.zone.values()]
        rx = max(max(xs) - min(xs), 1)
        ry = max(max(ys) - min(ys), 1)
        self.scale = max(
            min((WIN_W - 2 * PAD) // rx, (WIN_H - HUD_H - 2 * PAD) // ry, 110),
            40,
        )
        self.ox = (WIN_W - rx * self.scale) // 2 - min(xs) * self.scale
        self.oy = HUD_H + PAD - min(ys) * self.scale
        self.zr = max(10, min(18, self.scale // 4))  # zone radius
        self.dr = max(5, self.zr // 2)               # drone radius

    def _pos(self, x: int, y: int) -> Tuple[int, int]:
        return (x * self.scale + self.ox, y * self.scale + self.oy)

    def _zone_color(self, name: str) -> Tuple[int, int, int]:
        z = self.manager.zone.get(name)
        if z is None:
            return ZONE_COLORS["normal"]
        if z.is_start:
            return ZONE_COLORS["start"]
        if z.is_end:
            return ZONE_COLORS["end"]
        if z.zone_type == ZoneType.RESTRICTED:
            return ZONE_COLORS["restricted"]
        if z.zone_type == ZoneType.PRIORITY:
            return ZONE_COLORS["priority"]
        return ZONE_COLORS["normal"]

    def _draw_connections(self) -> None:
        seen: set[Tuple[str, str]] = set()
        for conns in self.manager.adjacency_list.values():
            for c in conns:
                a_name = c.prev_zone.name
                b_name = c.next_zone.name
                key: Tuple[str, str] = (
                    min(a_name, b_name),
                    max(a_name, b_name))
                if key in seen:
                    continue
                seen.add(key)
                a = self._pos(c.prev_zone.x, c.prev_zone.y)
                b = self._pos(c.next_zone.x, c.next_zone.y)
                pygame.draw.line(self.screen, GREY, a, b, 2)

    def _draw_zones(self) -> None:
        for z in self.manager.zone.values():
            pos = self._pos(z.x, z.y)
            pygame.draw.circle(self.screen,
                               self._zone_color(z.name),
                               pos,
                               self.zr)
            pygame.draw.circle(self.screen, WHITE, pos, self.zr, 2)
            lbl = self.font.render(z.name, True, (200, 200, 200))
            self.screen.blit(
                lbl,
                (pos[0] - lbl.get_width() // 2, pos[1] + self.zr + 3))

    def _draw_drones(self, snapshot: Dict[str, str]) -> None:
        # group drones by zone
        by_zone: Dict[str, List[str]] = {}
        for label, zone in snapshot.items():
            by_zone.setdefault(zone, []).append(label)

        sp = self.dr * 2 + 4  # spacing between drone circles
        for zone_name, labels in by_zone.items():
            z = self.manager.zone.get(zone_name)
            if z is None:
                continue
            cx, cy = self._pos(z.x, z.y)
            show = sorted(labels)[:6]
            n = len(show)
            for i, label in enumerate(show):
                px = cx + int((i - (n - 1) / 2) * sp)
                py = cy - self.zr - self.dr - 4
                pygame.draw.circle(self.screen, YELLOW, (px, py), self.dr)
                t = self.font.render(label, True, BLACK)
                self.screen.blit(
                    t,
                    (px - t.get_width() // 2, py - t.get_height() // 2))
            if len(labels) > 6:
                t = self.font.render(f"+{len(labels) - 6}", True, YELLOW)
                self.screen.blit(
                    t,
                    (cx + n * sp // 2 + 4, cy - self.zr - self.dr * 2))

    def _draw_hud(self, turn: int, total: int) -> None:
        status = "DONE" if turn == total else "running"
        t = self.hfont.render(
            f"Turn {turn} / {total}  ({status})", True, WHITE)
        self.screen.blit(t, (16, 10))
        legend = [
            ("Start", ZONE_COLORS["start"]),
            ("End", ZONE_COLORS["end"]),
            ("Normal", ZONE_COLORS["normal"]),
            ("Restricted", ZONE_COLORS["restricted"]),
            ("Priority", ZONE_COLORS["priority"]),
        ]
        lx = 16
        for name, color in legend:
            pygame.draw.circle(self.screen, color, (lx + 6, 48), 6)
            lbl = self.font.render(name, True, (200, 200, 200))
            self.screen.blit(lbl, (lx + 16, 41))
            lx += lbl.get_width() + 24

    def run(self) -> None:
        total = len(self.snapshots)
        turn = 0
        last_tick = pygame.time.get_ticks()
        running = True
        while running:
            now = pygame.time.get_ticks()
            if now - last_tick >= MS_PER_TURN and turn < total - 1:
                turn += 1
                last_tick = now
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_RIGHT and turn < total - 1:
                        turn += 1
                        last_tick = now
                    if event.key == pygame.K_LEFT and turn > 0:
                        turn -= 1
                        last_tick = now
            self.screen.fill(BG)
            self._draw_connections()
            self._draw_zones()
            self._draw_drones(self.snapshots[turn])
            self._draw_hud(turn + 1, total)
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
    except (FlyInError, FileNotFoundError) as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
    try:
        engine = EngineSimulation(parser.manager)
        _, snapshots = engine.run()
    except FlyInError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
    Visualizer(parser.manager, snapshots).run()


if __name__ == "__main__":
    main()
