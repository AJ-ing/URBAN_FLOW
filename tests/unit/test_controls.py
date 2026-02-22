"""Tests for ControlPanel."""

import os
import pytest
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.visualization.controls import ControlPanel, SPEEDS


@pytest.fixture
def panel():
    pygame.init()
    pygame.display.set_mode((1280, 100))
    p = ControlPanel(pygame.Rect(0, 0, 1280, 100))
    yield p
    pygame.quit()


def test_init(panel):
    assert panel.paused is True
    assert panel.speed == 1.0

def test_buttons_created(panel):
    names = [b["name"] for b in panel.buttons]
    assert "play_pause" in names
    assert "reset" in names
    assert "step" in names

def test_space_toggles_pause(panel):
    was_paused = panel.paused
    ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
    cmd = panel.handle_event(ev)
    assert cmd == "toggle_pause"
    assert panel.paused != was_paused

def test_r_resets(panel):
    ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)
    assert panel.handle_event(ev) == "reset"

def test_right_arrow_steps(panel):
    ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)
    assert panel.handle_event(ev) == "step"

def test_speed_clamped(panel):
    for _ in range(20):
        panel.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_EQUALS))
    assert panel.speed <= SPEEDS[-1]

    for _ in range(20):
        panel.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_MINUS))
    assert panel.speed >= SPEEDS[0]

def test_tick_update(panel):
    panel.update_tick(99)
    assert panel.tick == 99
