"""
Dashboard module for UrbanFlow traffic simulation.
Provides the main window, layout management, and the game loop
that ties together all the visual components.
"""

import pygame
import sys

# Window defaults
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60

# Layout sizes
SIDEBAR_W = 300
CONTROL_H = 80

# Dark theme colors
BG_COLOR = (15, 15, 35)
PANEL_COLOR = (26, 26, 46)
BORDER_COLOR = (50, 50, 80)
TEXT_COLOR = (224, 224, 224)
ACCENT_COLOR = (74, 158, 255)


class Dashboard:
    """
    Main dashboard window that manages the simulation visualization.
    Has 3 panels: network view (traffic grid), metrics sidebar, and control bar.
    """

    def __init__(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT):
        pygame.init()

        self.width = width
        self.height = height
        self.running = True
        self.paused = True
        self.sim_speed = 1.0
        self._demo_tick = 0

        self.screen = pygame.display.set_mode(
            (self.width, self.height), pygame.DOUBLEBUF | pygame.RESIZABLE
        )
        pygame.display.set_caption("UrbanFlow - Traffic Simulation")
        self.clock = pygame.time.Clock()

        # fonts
        self.font = pygame.font.SysFont("consolas", 14)
        self.font_med = pygame.font.SysFont("consolas", 18)

        # setup panel layout
        self.panels = {}
        self._setup_panels()

        # create the child components
        from src.visualization.traffic_renderer import TrafficRenderer
        from src.visualization.charts import MetricsChart
        from src.visualization.controls import ControlPanel

        self.renderer = TrafficRenderer(self.screen, self.panels["network"])
        self.charts = MetricsChart(self.panels["metrics"])
        self.controls = ControlPanel(self.panels["controls"])

    def _setup_panels(self):
        """Divides the window into 3 non-overlapping panel regions."""
        net_w = self.width - SIDEBAR_W
        net_h = self.height - CONTROL_H

        self.panels["network"] = pygame.Rect(0, 0, net_w, net_h)
        self.panels["metrics"] = pygame.Rect(net_w, 0, SIDEBAR_W, net_h)
        self.panels["controls"] = pygame.Rect(0, net_h, self.width, CONTROL_H)

    def handle_events(self):
        """Processes user input — keys, mouse, window events."""
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.w, event.h
                self.screen = pygame.display.set_mode(
                    (self.width, self.height), pygame.DOUBLEBUF | pygame.RESIZABLE
                )
                self._setup_panels()
                self.renderer.rect = self.panels["network"]
                self.renderer.surface = self.screen

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

            # pass events to child components
            self.renderer.handle_event(event)
            cmd = self.controls.handle_event(event)

            if cmd == "toggle_pause":
                self.paused = self.controls.paused
            elif cmd == "reset":
                self.charts.reset()
                self._demo_tick = 0
            elif cmd == "step":
                self._advance_demo()

        return events

    def _advance_demo(self):
        """Generates fake metric data for Phase 1 demo purposes."""
        import random

        self._demo_tick += 1
        self.controls.update_tick(self._demo_tick)

        # some random fluctuating values to show the charts working
        self.charts.update(
            {
                "throughput": 800 + random.uniform(-15, 15) * (self._demo_tick % 50),
                "avg_wait_time": 20
                + random.uniform(-2, 2) * (self._demo_tick % 30) / 10,
                "avg_queue_length": 5
                + random.uniform(-1, 1) * (self._demo_tick % 20) / 10,
            }
        )

    def update(self):
        """Called each frame — advances the simulation if not paused."""
        if not self.paused:
            self._advance_demo()

    def render(self):
        """Draws everything to the screen."""
        self.screen.fill(BG_COLOR)

        # draw panel backgrounds and borders
        for name, rect in self.panels.items():
            pygame.draw.rect(self.screen, PANEL_COLOR, rect)
            pygame.draw.rect(self.screen, BORDER_COLOR, rect, 1)

        # render each component
        self.renderer.render()
        self.charts.render(self.screen)
        self.controls.render(self.screen)

        # fps counter top-right
        fps = self.clock.get_fps()
        fps_color = (40, 167, 69) if fps >= 50 else (220, 53, 69)
        fps_surf = self.font.render(f"FPS: {fps:.0f}", True, fps_color)
        self.screen.blit(fps_surf, (self.width - 80, 8))

        # show pause message
        if self.paused:
            panel = self.panels["network"]
            msg = self.font_med.render(
                "PAUSED - Press Space to start", True, ACCENT_COLOR
            )
            msg_rect = msg.get_rect(centerx=panel.centerx, top=panel.top + 12)
            self.screen.blit(msg, msg_rect)

        pygame.display.flip()

    def run(self):
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    app = Dashboard()
    app.run()
