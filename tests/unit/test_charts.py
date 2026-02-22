"""Tests for MetricsChart."""

import os
import pytest
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.visualization.charts import MetricsChart, METRICS, HISTORY_LEN


@pytest.fixture
def chart():
    pygame.init()
    pygame.display.set_mode((400, 720))
    c = MetricsChart(pygame.Rect(0, 0, 400, 720))
    yield c
    pygame.quit()


def test_init(chart):
    assert chart.tick == 0
    for name in METRICS:
        assert len(chart.data[name]) == 0


def test_update_adds_data(chart):
    chart.update({"throughput": 100.0})
    assert len(chart.data["throughput"]) == 1
    assert chart.tick == 1


def test_deque_maxlen(chart):
    for i in range(HISTORY_LEN + 50):
        chart.update({"throughput": float(i)})
    assert len(chart.data["throughput"]) == HISTORY_LEN


def test_unknown_keys_ok(chart):
    chart.update({"blah": 42.0})
    assert chart.tick == 1


def test_reset(chart):
    chart.update({"throughput": 1.0, "avg_wait_time": 2.0})
    chart.reset()
    assert chart.tick == 0
    assert len(chart.data["throughput"]) == 0
