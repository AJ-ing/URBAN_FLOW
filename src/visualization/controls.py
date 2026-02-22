"""
Control panel for UrbanFlow simulation.
Play/Pause, Reset, Step buttons + speed slider + keyboard shortcuts.
"""

import pygame

BTN_W = 50
BTN_H = 44
BTN_GAP = 10
BTN_RADIUS = 8

SPEEDS = [0.5, 1.0, 2.0, 5.0, 10.0]

# control bar colors
C_BG = (20, 20, 40)
C_BTN = (45, 45, 75)
C_BTN_HOVER = (60, 60, 100)
C_BTN_PRESS = (35, 35, 60)
C_ICON = (224, 224, 224)
C_ICON_HL = (74, 158, 255)
C_SLIDER = (60, 60, 90)
C_KNOB = (74, 158, 255)
C_TEXT = (224, 224, 224)
C_DIM = (136, 136, 136)


class ControlPanel:
    """
    Bottom control bar with playback buttons, speed slider, and status text.
    Returns command strings when the user interacts with controls.
    """

    def __init__(self, rect):
        self.rect = rect
        self.paused = True
        self.speed_idx = 1
        self.speed = SPEEDS[self.speed_idx]
        self.tick = 0

        self.font = pygame.font.SysFont("consolas", 14)
        self.font_b = pygame.font.SysFont("consolas", 14, bold=True)
        self.font_s = pygame.font.SysFont("consolas", 11)

        self.dragging_slider = False
        self.hover_btn = None
        self.hover_since = 0

        # set up buttons and slider positions
        self.buttons = []
        self.slider_rect = None
        self._layout()

    def _layout(self):
        """Positions the buttons and slider within the control bar."""
        x = self.rect.x + 20
        y = self.rect.y + (self.rect.height - BTN_H) // 2

        for name, tip in [
            ("play_pause", "Play/Pause (Space)"),
            ("reset", "Reset (R)"),
            ("step", "Step (Right Arrow)"),
        ]:
            self.buttons.append(
                {
                    "name": name,
                    "tip": tip,
                    "rect": pygame.Rect(x, y, BTN_W, BTN_H),
                    "state": "normal",
                }
            )
            x += BTN_W + BTN_GAP

        # speed slider
        sx = x + 30
        sy = self.rect.y + self.rect.height // 2
        self.slider_rect = pygame.Rect(sx, sy - 2, 160, 4)

    def handle_event(self, event):
        """Process keyboard and mouse input, return command string or None."""

        # keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.paused = not self.paused
                return "toggle_pause"
            elif event.key == pygame.K_r:
                return "reset"
            elif event.key == pygame.K_RIGHT:
                return "step"
            elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                return self._change_speed(1)
            elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                return self._change_speed(-1)

        # mouse click
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.buttons:
                if btn["rect"].collidepoint(event.pos):
                    btn["state"] = "pressed"
                    return self._btn_click(btn["name"])

            if self.slider_rect and self.slider_rect.inflate(20, 20).collidepoint(
                event.pos
            ):
                self.dragging_slider = True
                self._slider_from_mouse(event.pos[0])
                return "speed_change"

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for btn in self.buttons:
                btn["state"] = "normal"
            self.dragging_slider = False

        # mouse move — hover states + slider drag
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_slider:
                self._slider_from_mouse(event.pos[0])
                return "speed_change"

            new_hover = None
            for btn in self.buttons:
                if btn["rect"].collidepoint(event.pos):
                    if btn["state"] != "pressed":
                        btn["state"] = "hover"
                    new_hover = btn["name"]
                elif btn["state"] == "hover":
                    btn["state"] = "normal"

            if new_hover != self.hover_btn:
                self.hover_btn = new_hover
                self.hover_since = pygame.time.get_ticks()

        return None

    def _btn_click(self, name):
        if name == "play_pause":
            self.paused = not self.paused
            return "toggle_pause"
        elif name == "reset":
            return "reset"
        elif name == "step":
            return "step"

    def _change_speed(self, direction):
        self.speed_idx = max(0, min(len(SPEEDS) - 1, self.speed_idx + direction))
        self.speed = SPEEDS[self.speed_idx]
        return "speed_change"

    def _slider_from_mouse(self, mx):
        """Maps mouse x position to a speed preset."""
        t = (mx - self.slider_rect.x) / self.slider_rect.width
        t = max(0.0, min(1.0, t))
        idx = round(t * (len(SPEEDS) - 1))
        self.speed_idx = idx
        self.speed = SPEEDS[self.speed_idx]

    def update_tick(self, tick):
        self.tick = tick

    def render(self, surface):
        """Draws the control bar."""
        pygame.draw.rect(surface, C_BG, self.rect)
        pygame.draw.line(
            surface,
            (50, 50, 80),
            (self.rect.x, self.rect.y),
            (self.rect.right, self.rect.y),
        )

        # buttons
        for btn in self.buttons:
            self._draw_btn(surface, btn)

        # slider
        self._draw_slider(surface)

        # status text on the right
        self._draw_status(surface)

        # tooltip
        self._draw_tooltip(surface)

    def _draw_btn(self, surface, btn):
        r = btn["rect"]
        st = btn["state"]
        col = {"normal": C_BTN, "hover": C_BTN_HOVER, "pressed": C_BTN_PRESS}[st]
        pygame.draw.rect(surface, col, r, border_radius=BTN_RADIUS)

        cx, cy = r.centerx, r.centery
        ic = C_ICON_HL if st == "hover" else C_ICON

        if btn["name"] == "play_pause":
            if self.paused:
                # play triangle
                pygame.draw.polygon(
                    surface, ic, [(cx - 6, cy - 8), (cx - 6, cy + 8), (cx + 8, cy)]
                )
            else:
                # pause bars
                pygame.draw.rect(surface, ic, (cx - 7, cy - 8, 5, 16))
                pygame.draw.rect(surface, ic, (cx + 2, cy - 8, 5, 16))
        elif btn["name"] == "reset":
            pygame.draw.rect(surface, ic, (cx - 7, cy - 7, 14, 14))
        elif btn["name"] == "step":
            pygame.draw.polygon(
                surface, ic, [(cx - 7, cy - 8), (cx - 7, cy + 8), (cx + 4, cy)]
            )
            pygame.draw.rect(surface, ic, (cx + 6, cy - 8, 3, 16))

    def _draw_slider(self, surface):
        if not self.slider_rect:
            return

        lbl = self.font_s.render("Speed", True, C_DIM)
        surface.blit(lbl, (self.slider_rect.x, self.slider_rect.y - 18))

        # track
        pygame.draw.rect(surface, C_SLIDER, self.slider_rect, border_radius=2)

        # knob position
        t = self.speed_idx / max(1, len(SPEEDS) - 1)
        kx = int(self.slider_rect.x + t * self.slider_rect.width)
        ky = self.slider_rect.centery

        # filled portion
        filled = pygame.Rect(
            self.slider_rect.x,
            self.slider_rect.y,
            kx - self.slider_rect.x,
            self.slider_rect.height,
        )
        pygame.draw.rect(surface, C_KNOB, filled, border_radius=2)

        # knob circle
        pygame.draw.circle(surface, C_KNOB, (kx, ky), 8)
        pygame.draw.circle(surface, C_BG, (kx, ky), 4)

        # speed label
        spd = self.font_b.render(f"{self.speed:.1f}x", True, C_KNOB)
        surface.blit(spd, (self.slider_rect.right + 10, self.slider_rect.y - 10))

    def _draw_status(self, surface):
        icon = "||" if self.paused else ">>"
        word = "PAUSED" if self.paused else "RUNNING"
        col = C_DIM if self.paused else (40, 220, 120)

        txt = f"{icon} {word}  |  Tick: {self.tick:,}"
        surf = self.font.render(txt, True, col)
        x = self.rect.right - surf.get_width() - 20
        y = self.rect.centery - surf.get_height() // 2
        surface.blit(surf, (x, y))

    def _draw_tooltip(self, surface):
        if self.hover_btn is None:
            return
        if pygame.time.get_ticks() - self.hover_since < 600:
            return

        btn = next((b for b in self.buttons if b["name"] == self.hover_btn), None)
        if not btn:
            return

        txt = self.font_s.render(btn["tip"], True, (224, 224, 224))
        pad = 6
        tr = pygame.Rect(
            btn["rect"].x,
            btn["rect"].y - txt.get_height() - pad * 2 - 5,
            txt.get_width() + pad * 2,
            txt.get_height() + pad * 2,
        )
        pygame.draw.rect(surface, (50, 50, 80), tr, border_radius=4)
        surface.blit(txt, (tr.x + pad, tr.y + pad))


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1280, 100))
    pygame.display.set_caption("ControlPanel Test")
    clock = pygame.time.Clock()

    cp = ControlPanel(pygame.Rect(0, 0, 1280, 100))
    tick = 0
    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            cmd = cp.handle_event(ev)
            if cmd:
                print(f"cmd={cmd} speed={cp.speed}x paused={cp.paused}")
        if not cp.paused:
            tick += 1
            cp.update_tick(tick)
        screen.fill((15, 15, 35))
        cp.render(screen)
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
