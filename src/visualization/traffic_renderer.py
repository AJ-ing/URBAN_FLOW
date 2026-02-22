"""
Traffic renderer for UrbanFlow.
Draws the top-down view of the traffic network — roads, lane markings,
vehicles, and traffic signals. Also handles zoom and pan.
"""

import pygame
import math

# Grid and road sizing
CELL_SIZE = 150  # px between intersections at zoom 1.0
ROAD_WIDTH = 40
DASH_LEN = 15
DASH_GAP = 10

# Vehicle sizing
VEH_LEN = 22
VEH_WID = 11

# Signal sizing
SIG_RADIUS = 9
GLOW_RADIUS = 20

# Zoom config
MIN_ZOOM = 0.3
MAX_ZOOM = 3.0

# Colors
ROAD_COL = (60, 60, 60)
MARKING_COL = (220, 220, 220)
INTERSECT_COL = (50, 50, 50)
GRASS_COL = (30, 55, 30)

VEH_COLORS = {
    "north": (74, 158, 255),
    "south": (255, 107, 107),
    "east": (255, 193, 7),
    "west": (40, 220, 120),
    "default": (200, 200, 200),
}

SIG_COLORS = {
    "red": {"on": (220, 50, 50), "off": (80, 20, 20)},
    "yellow": {"on": (240, 200, 50), "off": (80, 65, 20)},
    "green": {"on": (50, 200, 80), "off": (20, 70, 30)},
}


class TrafficRenderer:
    """
    Renders the traffic network view — roads, vehicles, signals.
    Handles zoom (scroll wheel) and pan (middle mouse drag).
    """

    def __init__(self, surface, rect):
        self.surface = surface
        self.rect = rect
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.zoom = 1.0
        self.panning = False

    def grid_to_screen(self, gx, gy):
        """Converts grid coordinates to pixel position on screen."""
        wx = gx * CELL_SIZE
        wy = gy * CELL_SIZE
        sx = int(wx * self.zoom + self.cam_x + self.rect.x + 50)
        sy = int(wy * self.zoom + self.cam_y + self.rect.y + 50)
        return sx, sy

    def scaled(self, val):
        """Scales a value by current zoom, min 1px."""
        return max(1, int(val * self.zoom))

    def handle_event(self, event):
        """Handles zoom and pan input."""
        if event.type == pygame.MOUSEWHEEL:
            mpos = pygame.mouse.get_pos()
            if self.rect.collidepoint(mpos):
                old_z = self.zoom
                self.zoom = max(MIN_ZOOM, min(MAX_ZOOM, self.zoom + event.y * 0.1))
                # zoom toward mouse pos (same idea as google maps zoom)
                ratio = self.zoom / old_z
                self.cam_x = mpos[0] - ratio * (mpos[0] - self.cam_x)
                self.cam_y = mpos[1] - ratio * (mpos[1] - self.cam_y)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
            if self.rect.collidepoint(event.pos):
                self.panning = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 2:
            self.panning = False
        elif event.type == pygame.MOUSEMOTION and self.panning:
            self.cam_x += event.rel[0]
            self.cam_y += event.rel[1]

    def render(self, state=None):
        """Main render method. Draws demo grid if no state provided."""
        self.surface.set_clip(self.rect)

        if state is None:
            self._draw_demo(3, 3)
        else:
            # Phase 2: render from actual sim state
            self._draw_from_state(state)

        self.surface.set_clip(None)

    def _draw_from_state(self, state):
        """Renders from real simulation data (Phase 2+)."""
        pygame.draw.rect(self.surface, GRASS_COL, self.rect)
        for sig in state.get("signals", []):
            self._draw_signals([sig])
        for veh in state.get("vehicles", []):
            self._draw_vehicles([veh])

    def _draw_demo(self, rows, cols):
        """Draws a demo grid with fake vehicles and signals for testing."""
        rw = self.scaled(ROAD_WIDTH)
        half = rw // 2

        # grass background
        pygame.draw.rect(self.surface, GRASS_COL, self.rect)

        # draw roads between intersections
        for r in range(rows):
            for c in range(cols):
                sx, sy = self.grid_to_screen(c, r)

                # horizontal road to the right
                if c < cols - 1:
                    nx, _ = self.grid_to_screen(c + 1, r)
                    pygame.draw.rect(
                        self.surface, ROAD_COL, (sx, sy - half, nx - sx, rw)
                    )
                    self._dashed_line((sx, sy), (nx, sy), MARKING_COL)

                # vertical road going down
                if r < rows - 1:
                    _, ny = self.grid_to_screen(c, r + 1)
                    pygame.draw.rect(
                        self.surface, ROAD_COL, (sx - half, sy, rw, ny - sy)
                    )
                    self._dashed_line((sx, sy), (sx, ny), MARKING_COL)

        # intersection boxes
        for r in range(rows):
            for c in range(cols):
                sx, sy = self.grid_to_screen(c, r)
                pygame.draw.rect(
                    self.surface, INTERSECT_COL, (sx - rw // 2, sy - rw // 2, rw, rw)
                )

        # demo signals
        signals = []
        for r in range(rows):
            for c in range(cols):
                if (r + c) % 2 == 0:
                    st = {"ns": "red", "ew": "green"}
                else:
                    st = {"ns": "green", "ew": "red"}
                signals.append({"grid_x": c, "grid_y": r, "state": st})
        self._draw_signals(signals)

        # some demo vehicles scattered around
        vehicles = [
            {"grid_x": 0.3, "grid_y": 0, "direction": "east"},
            {"grid_x": 0.6, "grid_y": 0, "direction": "east"},
            {"grid_x": 1, "grid_y": 0.4, "direction": "south"},
            {"grid_x": 2, "grid_y": 1.7, "direction": "south"},
            {"grid_x": 1.5, "grid_y": 1, "direction": "east"},
            {"grid_x": 0, "grid_y": 1.6, "direction": "south"},
            {"grid_x": 1.8, "grid_y": 2, "direction": "west"},
            {"grid_x": 1, "grid_y": 1.3, "direction": "south"},
            {"grid_x": 0.7, "grid_y": 2, "direction": "east"},
        ]
        self._draw_vehicles(vehicles)

    def _dashed_line(self, start, end, color):
        """Draws a dashed line between two points."""
        x1, y1 = start
        x2, y2 = end
        dx, dy = x2 - x1, y2 - y1
        dist = max(1, math.hypot(dx, dy))
        dl = self.scaled(DASH_LEN)
        dg = self.scaled(DASH_GAP)
        num_dashes = int(dist / (dl + dg))

        for i in range(num_dashes):
            t1 = i * (dl + dg) / dist
            t2 = min(1.0, (i * (dl + dg) + dl) / dist)
            p1 = (int(x1 + dx * t1), int(y1 + dy * t1))
            p2 = (int(x1 + dx * t2), int(y1 + dy * t2))
            pygame.draw.line(self.surface, color, p1, p2, 1)

    def _draw_vehicles(self, vehicles):
        """Draws vehicles as colored rectangles, rotated by direction."""
        vl = self.scaled(VEH_LEN)
        vw = self.scaled(VEH_WID)

        for v in vehicles:
            sx, sy = self.grid_to_screen(v["grid_x"], v["grid_y"])
            direction = v.get("direction", "default")
            color = VEH_COLORS.get(direction, VEH_COLORS["default"])

            # create vehicle surface
            veh_surf = pygame.Surface((vl, vw), pygame.SRCALPHA)
            veh_surf.fill(color)

            # small windshield highlight at the front
            hl_w = max(1, vl // 4)
            hl = pygame.Surface((hl_w, vw), pygame.SRCALPHA)
            hl.fill((255, 255, 255, 60))
            veh_surf.blit(hl, (vl - hl_w, 0))

            # rotate to face direction of travel
            angles = {"north": 90, "south": -90, "east": 0, "west": 180}
            rotated = pygame.transform.rotate(veh_surf, angles.get(direction, 0))
            rect = rotated.get_rect(center=(sx, sy))
            self.surface.blit(rotated, rect)

    def _draw_signals(self, signals):
        """Draws traffic signal circles at intersections with glow on green."""
        rad = self.scaled(SIG_RADIUS)
        glow_r = self.scaled(GLOW_RADIUS)
        offset = self.scaled(ROAD_WIDTH // 2 + 10)

        for sig in signals:
            sx, sy = self.grid_to_screen(sig["grid_x"], sig["grid_y"])
            state = sig.get("state", {"ns": "red", "ew": "red"})

            # north-south signal (above intersection)
            ns = state.get("ns", "red")
            ns_col = SIG_COLORS[ns]["on"]
            if ns == "green":
                self._glow(sx, sy - offset, glow_r, ns_col)
            pygame.draw.circle(self.surface, ns_col, (sx, sy - offset), rad)

            # east-west signal (right of intersection)
            ew = state.get("ew", "red")
            ew_col = SIG_COLORS[ew]["on"]
            if ew == "green":
                self._glow(sx + offset, sy, glow_r, ew_col)
            pygame.draw.circle(self.surface, ew_col, (sx + offset, sy), rad)

    def _glow(self, x, y, radius, color):
        """Draws a semi-transparent glow behind a signal light."""
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*color[:3], 50), (radius, radius), radius)
        self.surface.blit(surf, (x - radius, y - radius))


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("TrafficRenderer Test")
    clock = pygame.time.Clock()

    panel = pygame.Rect(0, 0, 980, 640)
    renderer = TrafficRenderer(screen, panel)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            renderer.handle_event(event)

        screen.fill((15, 15, 35))
        renderer.render()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
