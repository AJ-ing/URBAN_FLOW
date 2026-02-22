"""
Metrics charting for UrbanFlow.
Shows real-time line charts for throughput, wait time, and queue length
using matplotlib rendered onto pygame surfaces.
"""

import pygame
import io
from collections import deque

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HISTORY_LEN = 200
CHART_UPDATE_EVERY = 30   # only re-render chart every N ticks (performance)
CHART_DPI = 75
BG_COL = "#1a1a2e"

# what metrics we track and how to display them
METRICS = {
    "throughput": {"label": "Throughput (veh/hr)", "color": "#28a745", "unit": "veh/hr", "short": "Throughput"},
    "avg_wait_time": {"label": "Avg Wait Time (sec)", "color": "#dc3545", "unit": "sec", "short": "Wait Time"},
    "avg_queue_length": {"label": "Avg Queue Length", "color": "#4a9eff", "unit": "veh", "short": "Queue Len"},
}


class MetricsChart:
    """
    Collects metric data over time and renders line charts in the sidebar panel.
    Charts are rendered with matplotlib and cached as pygame surfaces to avoid
    re-rendering every single frame.
    """

    def __init__(self, rect, history=HISTORY_LEN):
        self.rect = rect
        self.history = history
        self.tick = 0
        self.cached_chart = None

        # deque with maxlen auto-drops old data when full
        self.data = {}
        for name in METRICS:
            self.data[name] = deque(maxlen=history)

        self.font_big = pygame.font.SysFont("consolas", 22, bold=True)
        self.font_sm = pygame.font.SysFont("consolas", 13)
        self.font_title = pygame.font.SysFont("consolas", 15, bold=True)

    def update(self, metrics):
        """Add new data point for each metric."""
        for name in METRICS:
            if name in metrics:
                self.data[name].append(metrics[name])

        self.tick += 1

        # re-render chart image periodically (not every frame — too slow)
        if self.tick % CHART_UPDATE_EVERY == 0:
            self._rebuild_chart()

    def _rebuild_chart(self):
        """Uses matplotlib to create chart images, saves to a pygame surface."""
        # figure out which metrics actually have data
        active = [n for n in METRICS if len(self.data[n]) > 1]
        if not active:
            return

        n_charts = len(active)
        fig_h = max(2, (self.rect.height - 140) / CHART_DPI)
        fig_w = max(2, (self.rect.width - 10) / CHART_DPI)

        fig, axes = plt.subplots(n_charts, 1, figsize=(fig_w, fig_h), facecolor=BG_COL)
        if n_charts == 1:
            axes = [axes]

        for ax, name in zip(axes, active):
            cfg = METRICS[name]
            vals = list(self.data[name])

            ax.set_facecolor(BG_COL)
            ax.plot(vals, color=cfg["color"], linewidth=1.5)
            ax.fill_between(range(len(vals)), vals, alpha=0.15, color=cfg["color"])
            ax.set_title(cfg["label"], color="#e0e0e0", fontsize=9, pad=4, loc="left")
            ax.tick_params(colors="#e0e0e0", labelsize=7)
            ax.grid(True, color="#2a2a4e", linewidth=0.5, alpha=0.5)
            for spine in ax.spines.values():
                spine.set_color("#2a2a4e")
            ax.set_xlim(0, self.history)

        plt.tight_layout(pad=0.5)

        # save chart to memory buffer and load as pygame surface
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=CHART_DPI, facecolor=BG_COL, edgecolor="none")
        plt.close(fig)  # important! otherwise memory leaks
        buf.seek(0)
        self.cached_chart = pygame.image.load(buf, "png").convert()
        buf.close()

    def render(self, surface):
        """Draws the metrics panel — numeric values on top, charts below."""
        pygame.draw.rect(surface, (26, 26, 46), self.rect)

        # panel heading
        title = self.font_title.render("METRICS", True, (74, 158, 255))
        surface.blit(title, (self.rect.x + 10, self.rect.y + 8))

        # current values for each metric
        y = self.rect.y + 32
        for name, cfg in METRICS.items():
            vals = self.data[name]
            cur = vals[-1] if vals else 0.0

            # label
            lbl = self.font_sm.render(cfg["short"], True, (136, 136, 136))
            surface.blit(lbl, (self.rect.x + 10, y))

            # value in metric color
            rgb = tuple(int(cfg["color"][i:i+2], 16) for i in (1, 3, 5))
            val_surf = self.font_big.render(f"{cur:.1f} {cfg['unit']}", True, rgb)
            surface.blit(val_surf, (self.rect.x + 10, y + 16))
            y += 42

        # the chart image itself
        if self.cached_chart:
            surface.blit(self.cached_chart, (self.rect.x + 5, self.rect.y + 165))

    def reset(self):
        """Clears all data — called on simulation reset."""
        for name in self.data:
            self.data[name].clear()
        self.tick = 0
        self.cached_chart = None


if __name__ == "__main__":
    import random

    pygame.init()
    screen = pygame.display.set_mode((400, 720))
    pygame.display.set_caption("MetricsChart Test")
    clock = pygame.time.Clock()

    chart = MetricsChart(pygame.Rect(0, 0, 400, 720))

    tp, wt, ql = 800.0, 20.0, 5.0
    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

        tp += random.uniform(-10, 12)
        wt += random.uniform(-1, 1.2)
        ql += random.uniform(-0.5, 0.6)
        tp, wt, ql = max(0, tp), max(0, wt), max(0, ql)

        chart.update({"throughput": tp, "avg_wait_time": wt, "avg_queue_length": ql})

        screen.fill((15, 15, 35))
        chart.render(screen)
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
