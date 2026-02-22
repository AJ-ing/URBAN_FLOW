"""Tests for the TrafficRenderer."""

import os
import pytest
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.visualization.traffic_renderer import TrafficRenderer, CELL_SIZE, VEH_COLORS, SIG_COLORS


@pytest.fixture
def renderer():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    r = TrafficRenderer(screen, pygame.Rect(0, 0, 600, 500))
    yield r
    pygame.quit()


def test_init(renderer):
    assert renderer.zoom == 1.0
    assert renderer.panning is False

def test_grid_to_screen_origin(renderer):
    sx, sy = renderer.grid_to_screen(0, 0)
    # should be near top-left with some margin
    assert 40 < sx < 60
    assert 40 < sy < 60

def test_grid_spacing(renderer):
    x0, _ = renderer.grid_to_screen(0, 0)
    x1, _ = renderer.grid_to_screen(1, 0)
    assert abs((x1 - x0) - CELL_SIZE) < 2

def test_zoom_doubles_spacing(renderer):
    renderer.zoom = 1.0
    x0, _ = renderer.grid_to_screen(0, 0)
    x1, _ = renderer.grid_to_screen(1, 0)
    d1 = x1 - x0

    renderer.zoom = 2.0
    x0, _ = renderer.grid_to_screen(0, 0)
    x1, _ = renderer.grid_to_screen(1, 0)
    d2 = x1 - x0
    assert abs(d2 - 2 * d1) < 2

def test_scale_min_1(renderer):
    renderer.zoom = 0.01
    assert renderer.scaled(1) >= 1

def test_vehicle_colors_exist():
    for d in ["north", "south", "east", "west"]:
        assert d in VEH_COLORS

def test_signal_colors_have_on_off():
    for s in ["red", "yellow", "green"]:
        assert "on" in SIG_COLORS[s]
        assert "off" in SIG_COLORS[s]
