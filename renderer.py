# Draws the whole right-side dashboard (sidebar).
# No state is kept here - state lives in dashboard_state.py.
# This file just reads from state and draws pixels.

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import pygame

import ui_theme as T
from dashboard_state import MODE_ADAPTIVE, MODE_FIXED, DashboardState

Rect = pygame.Rect


# --- helpers ---


def _round_rect(
    surface: pygame.Surface,
    color: Tuple[int, int, int],
    rect: Rect,
    radius: int = T.RADIUS,
    border: int = 0,
    border_color: Optional[Tuple[int, int, int]] = None,
) -> None:
    # filled rounded rect, with optional border on top
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border > 0 and border_color is not None:
        pygame.draw.rect(
            surface, border_color, rect, width=border, border_radius=radius
        )


def _format_time(seconds: float) -> str:
    # MM:SS format. zero-padded so width stays constant (layout doesn't jump)
    s = max(0, int(seconds))
    return f"{s // 60:02d}:{s % 60:02d}"


def _format_metric(value: float, decimals: int = 0) -> str:
    # adds K suffix for big numbers (10000 -> 10.0K) so they fit in the card
    if value is None:
        return "—"
    if value >= 10_000:
        return f"{value / 1000:.1f}K"
    if decimals == 0:
        return f"{int(value)}"
    return f"{value:.{decimals}f}"


def _catmull_rom_spline(
    points: List[Tuple[int, int]], samples_per_segment: int = 8
) -> List[Tuple[int, int]]:
    """Smooth out a jagged line by adding interpolated points between
    every original point. Looks way nicer than raw straight segments.

    I learned about this from a gamedev tutorial - it's a standard
    spline formula used in animation and path smoothing.
    """
    # need at least 4 points to do the interpolation (uses neighbors on both sides)
    if len(points) < 4:
        return points

    smoothed: List[Tuple[int, int]] = [points[0]]
    # for each segment between p1 and p2, look at p0 (before) and p3 (after)
    # to figure out how the curve should bend
    for i in range(1, len(points) - 2):
        p0, p1, p2, p3 = points[i - 1], points[i], points[i + 1], points[i + 2]
        for s in range(samples_per_segment):
            t = s / samples_per_segment
            t2 = t * t
            t3 = t2 * t
            # standard catmull-rom formula (looked this up on wikipedia)
            x = 0.5 * (
                (2 * p1[0])
                + (-p0[0] + p2[0]) * t
                + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
            )
            y = 0.5 * (
                (2 * p1[1])
                + (-p0[1] + p2[1]) * t
                + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
            )
            smoothed.append((int(x), int(y)))
    smoothed.append(points[-1])
    return smoothed


class Renderer:
    """Draws the dashboard. Reads from DashboardState, writes to pygame surface."""

    def __init__(self) -> None:
        # load all fonts once up front. _safe_font handles the case where
        # the user's system doesn't have Segoe UI installed
        self.font_value = self._safe_font(T.FONT_FAMILY, T.FONT_VALUE, bold=True)
        self.font_section = self._safe_font(T.FONT_FAMILY, T.FONT_SECTION, bold=True)
        self.font_label = self._safe_font(T.FONT_FAMILY, T.FONT_LABEL)
        self.font_body = self._safe_font(T.FONT_FAMILY, T.FONT_SIZE_BODY)
        self.font_body_bold = self._safe_font(
            T.FONT_FAMILY, T.FONT_SIZE_BODY, bold=True
        )
        self.font_small = self._safe_font(T.FONT_FAMILY, T.FONT_SM)
        self.font_tiny = self._safe_font(T.FONT_FAMILY, T.FONT_SIZE_TINY)
        self.font_timer = self._safe_font(T.FONT_FAMILY_MONO, 40, bold=True)
        self.font_brand = self._safe_font(T.FONT_FAMILY, 18, bold=True)

        # card positions computed once (they never change)
        self.rects: Dict[str, Rect] = {}
        self._layout()

        # these get rebuilt every frame as we draw buttons
        # (needed for mouse hit detection)
        self.button_rects: Dict[str, Rect] = {}
        # tracks how long each button has been hovered (for lift animation)
        self._hover_frames: Dict[str, int] = {}

    @staticmethod
    def _safe_font(family: str, size: int, bold: bool = False) -> pygame.font.Font:
        # tries the nice font, falls back to default pygame font if it's missing
        # (default font always works so this can't crash)
        try:
            return pygame.font.SysFont(family, size, bold=bold)
        except Exception:
            return pygame.font.Font(None, size)

    def _layout(self) -> None:
        # stack cards vertically from top to bottom
        # each card has a fixed height defined in ui_theme
        x = T.SIDEBAR_X + T.PANEL_PADDING
        w = T.SIDEBAR_WIDTH - 2 * T.PANEL_PADDING
        y = T.PANEL_PADDING

        self.rects["header"] = Rect(x, y, w, T.H_HEADER)
        y += T.H_HEADER + T.SECTION_GAP

        self.rects["stats"] = Rect(x, y, w, T.H_STATS)
        y += T.H_STATS + T.SECTION_GAP

        self.rects["chart"] = Rect(x, y, w, T.H_CHART)
        y += T.H_CHART + T.SECTION_GAP

        self.rects["controls"] = Rect(x, y, w, T.H_CONTROLS)
        y += T.H_CONTROLS + T.SECTION_GAP

        self.rects["mode"] = Rect(x, y, w, T.H_MODE)
        self.rects["export"] = Rect(
            x,
            T.WINDOW_HEIGHT - T.EXPORT_BOTTOM_PADDING - T.EXPORT_BUTTON_H,
            w,
            T.EXPORT_BUTTON_H,
        )

    # --- main draw call ---

    def draw_dashboard(
        self,
        surface: pygame.Surface,
        state: DashboardState,
        mouse_pos: Tuple[int, int],
    ) -> None:
        # paint sidebar bg first, then each card on top
        sidebar_rect = Rect(T.SIDEBAR_X, 0, T.SIDEBAR_WIDTH, T.WINDOW_HEIGHT)
        pygame.draw.rect(surface, T.BG_SIDEBAR, sidebar_rect)

        # 1px line separating sidebar from sim
        pygame.draw.line(
            surface, T.BORDER, (T.SIDEBAR_X, 0), (T.SIDEBAR_X, T.WINDOW_HEIGHT), 1
        )

        self.button_rects.clear()
        self._draw_title_bar(surface)
        self._draw_timer_card(surface, state)
        self._draw_stats_card(surface, state)
        self._draw_chart_card(surface, state)
        self._draw_controls_card(surface, state, mouse_pos)
        self._draw_mode_card(surface, state, mouse_pos)
        self._draw_footer_card(surface, state, mouse_pos)

    # --- each card ---

    def _draw_title_bar(self, surface: pygame.Surface) -> None:
        # app name on left, LIVE indicator on right
        r = self.rects["header"]

        brand = self.font_brand.render(T.APP_NAME, True, T.TEXT_PRIMARY)
        surface.blit(brand, (r.x, r.y))

        # small teal dot as a separator between name and version
        dot_x = r.x + brand.get_width() + 8
        pygame.draw.circle(surface, T.ACCENT, (dot_x + 3, r.y + 10), 3)

        version = self.font_small.render(T.APP_VERSION, True, T.TEXT_MUTED)
        surface.blit(version, (dot_x + 14, r.y + 4))

        # green pulse + "LIVE" text on the right
        live_x = r.right - 52
        pygame.draw.circle(surface, T.STATUS_PLAY, (live_x, r.y + 10), 4)
        live_txt = self.font_small.render("LIVE", True, T.STATUS_PLAY)
        surface.blit(live_txt, (live_x + 8, r.y + 4))

    def _draw_timer_card(self, surface: pygame.Surface, state: DashboardState) -> None:
        # elapsed timer and run state share the compact header
        r = self.rects["header"]

        cap = self.font_section.render("ELAPSED TIME", True, T.TEXT_MUTED)
        surface.blit(cap, (r.x, r.y + 42))

        timer_str = _format_time(state.elapsed_sim_time)
        ts = self.font_timer.render(timer_str, True, T.TEXT_PRIMARY)
        surface.blit(ts, (r.x, r.y + 58))

        # status pill changes color based on play state
        status_text = "RUNNING" if state.is_playing else "PAUSED"
        status_color = T.STATUS_PLAY if state.is_playing else T.STATUS_PAUSE

        # small colored dot next to the status text
        dot_y = r.y + 48
        pygame.draw.circle(surface, status_color, (r.right - 74, dot_y), 4)
        pill = self.font_small.render(status_text, True, status_color)
        surface.blit(pill, (r.right - pill.get_width(), r.y + 42))

        self._draw_divider(surface, r.bottom + T.SECTION_GAP // 2)

    def _draw_stats_card(self, surface: pygame.Surface, state: DashboardState) -> None:
        # 2x2 grid of the 4 live metrics from pod 3
        r = self.rects["stats"]

        hdr = self.font_section.render("LIVE METRICS", True, T.TEXT_SECONDARY)
        surface.blit(hdr, (r.x, r.y))

        snap = state.latest_snapshot

        # (label, value, unit) for each cell
        cells = [
            ("Throughput", _format_metric(snap["throughput"], 0), "veh/hr"),
            ("Queue", _format_metric(snap["queue_length"], 0), "vehicles"),
            ("Avg Wait", _format_metric(snap["avg_wait"], 1), "seconds"),
            ("Avg Travel", _format_metric(snap["avg_travel"], 1), "seconds"),
        ]

        cell_w = (r.width - T.METRIC_CARD_GAP) // 2
        for i, (label, value, unit) in enumerate(cells):
            row, col = divmod(i, 2)
            cx = r.x + col * (cell_w + T.METRIC_CARD_GAP)
            cy = r.y + 22 + row * (T.METRIC_CARD_H + T.METRIC_CARD_GAP)
            cell = Rect(cx, cy, cell_w, T.METRIC_CARD_H)
            _round_rect(surface, T.BG_METRIC_CARD, cell, radius=T.CARD_RADIUS)

            lbl = self.font_small.render(label.upper(), True, T.TEXT_MUTED)
            surface.blit(lbl, (cell.x + T.METRIC_PAD_X, cell.y + T.METRIC_PAD_Y))

            val_surf = self.font_value.render(value, True, T.ACCENT)
            surface.blit(
                val_surf,
                (
                    cell.x + T.METRIC_PAD_X,
                    cell.y + T.METRIC_PAD_Y + self.font_small.get_height(),
                ),
            )

            unit_s = self.font_label.render(unit, True, T.TEXT_DISABLED)
            surface.blit(
                unit_s,
                (
                    cell.right - unit_s.get_width() - T.METRIC_PAD_X,
                    cell.bottom - unit_s.get_height() - T.METRIC_PAD_Y,
                ),
            )

        self._draw_divider(surface, r.bottom + T.SECTION_GAP // 2)

    def _draw_chart_card(self, surface: pygame.Surface, state: DashboardState) -> None:
        # live throughput chart, last 120 seconds
        r = self.rects["chart"]

        hdr = self.font_section.render(
            "THROUGHPUT  ·  last 120s", True, T.TEXT_SECONDARY
        )
        surface.blit(hdr, (r.x, r.y))

        # the plot area (inset from the card)
        plot = Rect(r.x, r.y + 22, r.width, r.height - 22)
        _round_rect(surface, T.BG_INPUT, plot, radius=T.CARD_RADIUS)

        values = state.chart_values()
        # at the very start there's no data yet, so show a placeholder
        if len(values) < 2:
            msg = self.font_small.render("collecting data…", True, T.TEXT_DISABLED)
            surface.blit(
                msg,
                (
                    plot.centerx - msg.get_width() // 2,
                    plot.centery - msg.get_height() // 2,
                ),
            )
            self._draw_divider(surface, r.bottom + T.SECTION_GAP // 2)
            return

        # auto-scale y axis to fit data. force a minimum of 100 so an
        # empty/zero reading doesn't make the chart look silly
        y_max = max(values + [100.0])
        y_min = 0.0

        # horizontal grid lines at 1/3 and 2/3 height
        for i in range(1, 3):
            gy = plot.y + i * plot.height // 3
            pygame.draw.line(
                surface, T.CHART_GRID, (plot.x + 4, gy), (plot.right - 4, gy), 1
            )

        # convert data values to pixel coordinates
        n = len(values)
        raw_pts: List[Tuple[int, int]] = []
        for i, v in enumerate(values):
            x = plot.x + 4 + int(i * (plot.width - 8) / max(1, n - 1))
            # y is flipped in pygame (0 is top) so we subtract from bottom
            y_norm = (v - y_min) / max(1.0, (y_max - y_min))
            y = plot.bottom - 4 - int(y_norm * (plot.height - 8))
            raw_pts.append((x, y))

        # smooth the line so it looks professional instead of zig-zaggy
        smooth_pts = _catmull_rom_spline(raw_pts, samples_per_segment=10)

        if len(smooth_pts) >= 2:
            # draw a filled polygon under the line for a gradient-ish effect
            # need to close it by going back down to the baseline
            poly = smooth_pts + [
                (smooth_pts[-1][0], plot.bottom - 2),
                (smooth_pts[0][0], plot.bottom - 2),
            ]
            # drawing on a separate surface so we can use alpha for transparency
            fill_surf = pygame.Surface((plot.width, plot.height), pygame.SRCALPHA)
            # polygon coords need to be relative to fill_surf (not plot)
            local_poly = [(x - plot.x, y - plot.y) for (x, y) in poly]
            pygame.draw.polygon(fill_surf, (0, 212, 170, 45), local_poly)
            surface.blit(fill_surf, (plot.x, plot.y))

            # draw line twice - aalines for smooth edges, lines for thickness
            pygame.draw.aalines(surface, T.CHART_LINE, False, smooth_pts)
            pygame.draw.lines(surface, T.CHART_LINE, False, smooth_pts, 2)

            # small dot markers on the real data points (not the interpolated ones)
            # show every Nth so it's not a solid line of dots
            stride = max(1, len(raw_pts) // 12)
            for i in range(0, len(raw_pts), stride):
                # dark inner circle so the dot stands out against the line
                pygame.draw.circle(surface, T.BG_INPUT, raw_pts[i], 3)
                pygame.draw.circle(surface, T.CHART_LINE, raw_pts[i], 2)

            # current value shown as a little pill in the top-right of the chart
            latest = self.font_small.render(f"{int(values[-1])} veh/hr", True, T.ACCENT)
            pill_w = latest.get_width() + 12
            pill_h = latest.get_height() + 4
            pill_rect = Rect(plot.right - pill_w - 4, plot.y + 4, pill_w, pill_h)
            _round_rect(
                surface,
                T.BG_CARD,
                pill_rect,
                radius=4,
                border=1,
                border_color=T.ACCENT_DIM,
            )
            surface.blit(latest, (pill_rect.x + 6, pill_rect.y + 2))

        self._draw_divider(surface, r.bottom + T.SECTION_GAP // 2)

    def _draw_controls_card(
        self,
        surface: pygame.Surface,
        state: DashboardState,
        mouse: Tuple[int, int],
    ) -> None:
        # compact 2x2 transport controls
        r = self.rects["controls"]

        hdr = self.font_section.render("PLAYBACK", True, T.TEXT_SECONDARY)
        surface.blit(hdr, (r.x, r.y))

        btn_w = (r.width - T.CONTROL_GAP) // 2
        row_y = r.y + 20
        second_y = row_y + T.BUTTON_H + T.CONTROL_GAP

        play_rect = Rect(r.x, row_y, btn_w, T.BUTTON_H)
        self._draw_button(
            surface,
            play_rect,
            "▶  PLAY",
            mouse,
            key="play",
            primary=state.is_playing,
        )

        pause_rect = Rect(r.x + btn_w + T.CONTROL_GAP, row_y, btn_w, T.BUTTON_H)
        self._draw_button(
            surface,
            pause_rect,
            "⏸  PAUSE",
            mouse,
            key="pause",
            primary=not state.is_playing,
        )

        step_rect = Rect(r.x, second_y, btn_w, T.BUTTON_H)
        self._draw_button(
            surface,
            step_rect,
            "⏭  STEP",
            mouse,
            key="step",
            disabled=state.is_playing,
        )

        reset_rect = Rect(r.x + btn_w + T.CONTROL_GAP, second_y, btn_w, T.BUTTON_H)
        self._draw_button(
            surface,
            reset_rect,
            "⟲  RESET",
            mouse,
            key="reset",
        )

        self._draw_divider(surface, r.bottom + T.SECTION_GAP // 2)

    def _draw_mode_card(
        self,
        surface: pygame.Surface,
        state: DashboardState,
        mouse: Tuple[int, int],
    ) -> None:
        # two-pill toggle: FIXED vs ADAPTIVE
        r = self.rects["mode"]

        hdr = self.font_section.render("CONTROLLER MODE", True, T.TEXT_SECONDARY)
        surface.blit(hdr, (r.x, r.y))

        pill_w = (r.width - T.CONTROL_GAP) // 2
        pill_y = r.y + 22

        fixed_rect = Rect(r.x, pill_y, pill_w, T.MODE_BUTTON_H)
        adapt_rect = Rect(
            r.x + pill_w + T.CONTROL_GAP,
            pill_y,
            pill_w,
            T.MODE_BUTTON_H,
        )

        # active pill gets filled with color, inactive is just outlined
        self._draw_pill(
            surface,
            fixed_rect,
            "FIXED  (F)",
            mouse,
            key="mode_fixed",
            active=(state.controller_mode == MODE_FIXED),
            active_color=T.ACCENT,
        )
        self._draw_pill(
            surface,
            adapt_rect,
            "ADAPTIVE  (A)",
            mouse,
            key="mode_adaptive",
            active=(state.controller_mode == MODE_ADAPTIVE),
            active_color=T.ACCENT,
        )
        self._draw_divider(surface, r.bottom + T.SECTION_GAP // 2)

    def _draw_footer_card(
        self,
        surface: pygame.Surface,
        state: DashboardState,
        mouse: Tuple[int, int],
    ) -> None:
        # Full-width action remains pinned to the panel's bottom edge.
        exp_rect = self.rects["export"]
        self._draw_button(
            surface,
            exp_rect,
            "⬇  EXPORT CSV",
            mouse,
            key="export",
            primary=True,
            disabled=not state.export_enabled,
        )

    def _draw_attribution_strip(self, surface: pygame.Surface) -> None:
        # Kept for API compatibility; the pinned export action now owns the footer.
        y = T.WINDOW_HEIGHT - 18
        pygame.draw.line(
            surface,
            T.BORDER,
            (T.SIDEBAR_X + T.PADDING, y - 4),
            (T.SIDEBAR_X + T.SIDEBAR_WIDTH - T.PADDING, y - 4),
            1,
        )
        txt = self.font_tiny.render(T.AUTHOR_LINE, True, T.TEXT_DISABLED)
        surface.blit(
            txt,
            (T.SIDEBAR_X + (T.SIDEBAR_WIDTH - txt.get_width()) // 2, y),
        )

    # --- reusable button + pill ---

    def _draw_button(
        self,
        surface: pygame.Surface,
        rect: Rect,
        label: str,
        mouse: Tuple[int, int],
        key: str,
        primary: bool = False,
        disabled: bool = False,
    ) -> None:
        # one button with hover animation (smooth lift up on hover)
        hovered = rect.collidepoint(mouse) and not disabled

        # this counter goes up while hovered, down when not
        # gives us a smooth fade-in/fade-out instead of snapping
        prev = self._hover_frames.get(key, 0)
        if hovered:
            self._hover_frames[key] = min(T.TRANSITION_FRAMES, prev + 1)
        else:
            self._hover_frames[key] = max(0, prev - 1)
        lift = int(T.HOVER_LIFT_PX * self._hover_frames[key] / T.TRANSITION_FRAMES)

        # button moves up when hovered (y decreases = up on screen)
        draw_rect = rect.move(0, -lift)
        # but we save the ORIGINAL rect for click detection
        # (otherwise the button would "dodge" the cursor as you hover)
        self.button_rects[key] = rect

        # pick colors based on state
        if disabled:
            bg = T.BG_INPUT
            fg = T.TEXT_DISABLED
            border = T.BORDER
        elif primary:
            bg = T.ACCENT_DIM if hovered else T.ACCENT
            fg = T.BG_MAIN
            border = T.ACCENT
        else:
            bg = T.BG_CARD_HOVER if hovered else T.BG_INPUT
            fg = T.TEXT_PRIMARY
            border = T.BORDER_ACTIVE if hovered else T.BORDER

        # drop shadow appears under button when it's lifted up
        # (makes it look like it's actually floating off the card)
        if lift > 0:
            shadow = pygame.Surface((rect.width + 6, rect.height + 6), pygame.SRCALPHA)
            pygame.draw.rect(
                shadow,
                (0, 0, 0, 60),
                shadow.get_rect(),
                border_radius=T.CARD_RADIUS,
            )
            surface.blit(shadow, (draw_rect.x - 3, draw_rect.y + lift))

        _round_rect(
            surface, bg, draw_rect, radius=T.CARD_RADIUS, border=1, border_color=border
        )
        # center the text inside the button
        # Pygame's platform font fallback is inconsistent for transport glyphs.
        # Keep the semantic labels at call sites and render clean ASCII fallbacks
        # instead of missing-glyph boxes on machines without an emoji font.
        display_label = label
        for symbol, fallback in {
            "▶": ">",
            "⏸": "||",
            "⏭": ">>",
            "⟲": "R",
            "⬇": "v",
            "−": "-",
        }.items():
            display_label = display_label.replace(symbol, fallback)
        txt = self.font_small.render(display_label, True, fg)
        surface.blit(
            txt,
            (
                draw_rect.centerx - txt.get_width() // 2,
                draw_rect.centery - txt.get_height() // 2,
            ),
        )

    def _draw_pill(
        self,
        surface: pygame.Surface,
        rect: Rect,
        label: str,
        mouse: Tuple[int, int],
        key: str,
        active: bool,
        active_color: Tuple[int, int, int],
    ) -> None:
        # pill button for mode toggle (more rounded than regular button)
        self.button_rects[key] = rect
        hovered = rect.collidepoint(mouse)

        if active:
            # filled with the mode's color when active
            bg = active_color
            fg = T.BG_MAIN
            border = active_color
        else:
            bg = T.BG_SIDEBAR
            fg = T.TEXT_SECONDARY if hovered else T.TEXT_MUTED
            border = T.BORDER_ACTIVE if hovered else T.BORDER

        _round_rect(
            surface,
            bg,
            rect,
            radius=T.MODE_BUTTON_RADIUS,
            border=1,
            border_color=border,
        )
        txt = self.font_section.render(label, True, fg)
        surface.blit(
            txt,
            (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2),
        )

    # --- click handling ---

    def hit_test_button(self, pos: Tuple[int, int]) -> Optional[str]:
        # check all button rects and return which one (if any) was clicked
        for key, rect in self.button_rects.items():
            if rect.collidepoint(pos):
                return key
        return None

    def _draw_divider(self, surface: pygame.Surface, y: int) -> None:
        pygame.draw.line(
            surface,
            T.DIVIDER_COLOR,
            (T.SIDEBAR_X + T.PANEL_PADDING, y),
            (T.SIDEBAR_X + T.SIDEBAR_WIDTH - T.PANEL_PADDING, y),
            1,
        )
