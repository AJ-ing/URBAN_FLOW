# Holds all the styling stuff - colors, fonts, sizes, spacing
# Keeping everything here so if I want to tweak a color I change it in one place
# and the whole dashboard updates

from __future__ import annotations

# --- window size ---
# The simulation is 1400x800 (hardcoded in simulation.py, can't change it
# without breaking all the vehicle coordinates). So I just add my sidebar
# to the right side.
SIM_WIDTH: int = 1400
SIM_HEIGHT: int = 800
SIDEBAR_WIDTH: int = 360
WINDOW_WIDTH: int = SIM_WIDTH + SIDEBAR_WIDTH  # total = 1760
WINDOW_HEIGHT: int = SIM_HEIGHT

SIDEBAR_X: int = SIM_WIDTH  # where sidebar starts (right after sim)
PANEL_PADDING: int = 12
SECTION_GAP: int = 14
CARD_RADIUS: int = 6
BUTTON_H: int = 32
BUTTON_W_SMALL: int = 28

# Backwards-compatible aliases for generic drawing helpers.
PADDING: int = PANEL_PADDING
GUTTER: int = SECTION_GAP
RADIUS: int = CARD_RADIUS

# --- colors ---
# went with a dark navy + teal theme. Teal is only used for active/important
# things so it actually catches the eye

# backgrounds (darkest to lightest)
BG_MAIN = (13, 27, 42)
BG_SIDEBAR = (17, 34, 51)
BG_CARD = (26, 46, 64)
BG_METRIC_CARD = (
    min(BG_SIDEBAR[0] + 10, 255),
    min(BG_SIDEBAR[1] + 10, 255),
    min(BG_SIDEBAR[2] + 10, 255),
)
BG_CARD_HOVER = (33, 58, 80)  # slightly lighter when hovered
BG_INPUT = (10, 20, 30)  # darker for chart bg / input fields

BORDER = (40, 60, 80)
BORDER_ACTIVE = (0, 212, 170)

# text - 3 levels of emphasis
TEXT_PRIMARY = (232, 244, 248)
TEXT_SECONDARY = (164, 188, 205)
TEXT_MUTED = (122, 158, 181)
TEXT_DISABLED = (80, 100, 115)

# the one accent color
ACCENT = (0, 212, 170)  # teal #00D4AA
ACCENT_DIM = (0, 122, 98)  # darker for hover/pressed
ACCENT_GLOW = (0, 212, 170, 60)  # with alpha, for chart fill

# state colors
STATUS_PLAY = (74, 222, 128)  # green when running
STATUS_PAUSE = (251, 191, 36)  # amber when paused
STATUS_STOP = (248, 113, 113)  # red for errors
MODE_FIXED_COLOR = (251, 191, 36)
MODE_ADAPTIVE_COLOR = (74, 222, 128)

# chart colors
CHART_LINE = ACCENT
CHART_GRID = (35, 55, 75)
CHART_AXIS = (60, 85, 105)

# --- fonts ---
# using Segoe UI cause its on every windows machine and looks clean
# mono font for numbers so they don't jump around as digits change
FONT_FAMILY: str = "Segoe UI"
FONT_FAMILY_MONO: str = "Consolas"

FONT_SIZE_HERO: int = 36  # the big stat numbers
FONT_SIZE_LARGE: int = 22
FONT_SIZE_BODY: int = 15
FONT_SIZE_SMALL: int = 12
FONT_SIZE_TINY: int = 10

FONT_HEADER: int = 15
FONT_SECTION: int = 11
FONT_VALUE: int = 22
FONT_LABEL: int = 10
FONT_SM: int = FONT_SECTION
FONT_LG: int = FONT_VALUE

# --- card heights ---
# these add up to ~800 with padding. had to tweak these a few times
# to get everything to fit without looking cramped
H_HEADER: int = 120
H_STATS: int = 134
H_CHART: int = 210
H_CONTROLS: int = 92
H_MODE: int = 60
H_EXPORT: int = 36

# Right-panel component dimensions.
METRIC_CARD_H: int = 52
METRIC_CARD_GAP: int = 6
METRIC_PAD_X: int = 8
METRIC_PAD_Y: int = 6
CONTROL_GAP: int = 8
MODE_BUTTON_H: int = 30
MODE_BUTTON_RADIUS: int = 4
EXPORT_BUTTON_H: int = 36
EXPORT_BOTTOM_PADDING: int = 10
DIVIDER_COLOR = (77, 77, 77)  # approximately 30% white

# --- hover animation ---
HOVER_LIFT_PX: int = 2  # how much buttons move up when hovered
BTN_PRESS_DEPTH: int = 1
TRANSITION_FRAMES: int = 6  # smoothness of the lift animation

# --- branding ---
APP_NAME: str = "URBANFLOW"
APP_VERSION: str = "v1.0"
AUTHOR_LINE: str = "Built by Rushil Shandil"

H_TITLE: int = 36
