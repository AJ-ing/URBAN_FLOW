"""Tests for the Dashboard module."""

import os
import pytest
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.visualization.dashboard import Dashboard, SIDEBAR_W, CONTROL_H


@pytest.fixture
def dash():
    pygame.init()
    d = Dashboard(width=800, height=600)
    yield d
    pygame.quit()


def test_dashboard_init(dash):
    assert dash is not None
    assert dash.width == 800
    assert dash.height == 600

def test_starts_paused(dash):
    assert dash.paused is True
    assert dash.running is True

def test_all_panels_created(dash):
    assert "network" in dash.panels
    assert "metrics" in dash.panels
    assert "controls" in dash.panels

def test_panels_dont_overlap(dash):
    panels = list(dash.panels.values())
    for i in range(len(panels)):
        for j in range(i + 1, len(panels)):
            assert not panels[i].colliderect(panels[j])

def test_panel_sizes(dash):
    assert dash.panels["controls"].height == CONTROL_H
    assert dash.panels["metrics"].width == SIDEBAR_W
    assert dash.panels["network"].width == 800 - SIDEBAR_W

def test_quit_event(dash):
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    dash.handle_events()
    assert dash.running is False

def test_escape_closes(dash):
    ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
    pygame.event.post(ev)
    dash.handle_events()
    assert dash.running is False
