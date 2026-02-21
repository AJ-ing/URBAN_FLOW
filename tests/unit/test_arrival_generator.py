"""Unit tests for :mod:`src.simulation.arrival_generator`."""

import math
from collections import Counter
from unittest.mock import patch

import pytest

from src.simulation.arrival_generator import ArrivalGenerator
from src.simulation.vehicle import Vehicle


# ======================================================================
# Construction / defaults
# ======================================================================

class TestArrivalGeneratorInit:
    """Tests for ArrivalGenerator construction and defaults."""

    def test_default_attributes(self):
        """Generator with defaults should have lambda=1.0."""
        gen = ArrivalGenerator()
        assert gen.lambda_rate == 1.0
        assert gen.spawn_position == (0.0, 0.0)
        assert gen.spawn_lane == 0
        assert gen.default_speed == 13.9

    def test_custom_attributes(self):
        """All constructor parameters should be stored correctly."""
        gen = ArrivalGenerator(
            lambda_rate=3.5,
            spawn_position=(10.0, 20.0),
            spawn_lane=2,
            default_speed=30.0,
            seed=123,
        )
        assert gen.lambda_rate == 3.5
        assert gen.spawn_position == (10.0, 20.0)
        assert gen.spawn_lane == 2
        assert gen.default_speed == 30.0

    def test_negative_lambda_raises(self):
        """A negative lambda_rate should raise ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            ArrivalGenerator(lambda_rate=-1.0)

    def test_zero_lambda_is_valid(self):
        """lambda_rate of 0 should be accepted (no arrivals)."""
        gen = ArrivalGenerator(lambda_rate=0.0)
        assert gen.lambda_rate == 0.0


# ======================================================================
# generate_arrivals
# ======================================================================

class TestGenerateArrivals:
    """Tests for :meth:`ArrivalGenerator.generate_arrivals`."""

    def test_returns_list_of_vehicles(self):
        """Every element returned should be a Vehicle instance."""
        gen = ArrivalGenerator(lambda_rate=3.0, seed=42)
        vehicles = gen.generate_arrivals()
        assert isinstance(vehicles, list)
        assert all(isinstance(v, Vehicle) for v in vehicles)

    def test_zero_rate_produces_no_vehicles(self):
        """With λ=0 the Poisson distribution should always yield 0."""
        gen = ArrivalGenerator(lambda_rate=0.0, seed=1)
        for _ in range(100):
            assert gen.generate_arrivals() == []

    def test_vehicles_have_unique_ids(self):
        """IDs across multiple calls must be unique."""
        gen = ArrivalGenerator(lambda_rate=5.0, seed=7)
        all_ids = []
        for _ in range(20):
            all_ids.extend(v.id for v in gen.generate_arrivals())
        assert len(all_ids) == len(set(all_ids))

    def test_vehicles_use_spawn_position_and_lane(self):
        """Created vehicles should inherit spawn_position and spawn_lane."""
        gen = ArrivalGenerator(
            lambda_rate=5.0,
            spawn_position=(5.0, 10.0),
            spawn_lane=3,
            seed=42,
        )
        vehicles = gen.generate_arrivals()
        for v in vehicles:
            assert v.position == (5.0, 10.0)
            assert v.lane == 3

    def test_vehicles_use_default_speed(self):
        """Created vehicles should inherit the default_speed."""
        gen = ArrivalGenerator(
            lambda_rate=5.0,
            default_speed=25.0,
            seed=42,
        )
        vehicles = gen.generate_arrivals()
        for v in vehicles:
            assert v.speed == 25.0

    def test_destination_is_assigned(self):
        """Passing a destination should propagate to every vehicle."""
        gen = ArrivalGenerator(lambda_rate=5.0, seed=42)
        dest = (100.0, 200.0)
        vehicles = gen.generate_arrivals(destination=dest)
        for v in vehicles:
            assert v.destination == dest

    def test_destination_defaults_to_none(self):
        """Without a destination, vehicles should have None."""
        gen = ArrivalGenerator(lambda_rate=5.0, seed=42)
        vehicles = gen.generate_arrivals()
        for v in vehicles:
            assert v.destination is None

    def test_seed_reproducibility(self):
        """Two generators with the same seed should produce the same output."""
        gen_a = ArrivalGenerator(lambda_rate=3.0, seed=99)
        gen_b = ArrivalGenerator(lambda_rate=3.0, seed=99)
        for _ in range(50):
            a = [v.id for v in gen_a.generate_arrivals()]
            b = [v.id for v in gen_b.generate_arrivals()]
            assert len(a) == len(b)

    def test_poisson_mean_approximation(self):
        """Over many samples the mean should approximate lambda_rate."""
        lam = 4.0
        gen = ArrivalGenerator(lambda_rate=lam, seed=0)
        counts = [len(gen.generate_arrivals()) for _ in range(5000)]
        sample_mean = sum(counts) / len(counts)
        # Allow generous tolerance for statistical test
        assert abs(sample_mean - lam) < 0.3


# ======================================================================
# get_config
# ======================================================================

class TestGetConfig:
    """Tests for :meth:`ArrivalGenerator.get_config`."""

    def test_config_keys(self):
        """Config dict should contain exactly the expected keys."""
        gen = ArrivalGenerator()
        config = gen.get_config()
        assert set(config.keys()) == {
            "lambda_rate", "spawn_position", "spawn_lane", "default_speed",
        }

    def test_config_values_match(self):
        """Config values should match the generator's attributes."""
        gen = ArrivalGenerator(
            lambda_rate=2.0,
            spawn_position=(1.0, 2.0),
            spawn_lane=1,
            default_speed=20.0,
        )
        config = gen.get_config()
        assert config["lambda_rate"] == 2.0
        assert config["spawn_position"] == (1.0, 2.0)
        assert config["spawn_lane"] == 1
        assert config["default_speed"] == 20.0


# ======================================================================
# reset
# ======================================================================

class TestReset:
    """Tests for :meth:`ArrivalGenerator.reset`."""

    def test_id_counter_resets(self):
        """After reset, vehicle IDs should start from 0 again."""
        gen = ArrivalGenerator(lambda_rate=5.0, seed=42)
        gen.generate_arrivals()  # advances _next_id
        gen.reset(seed=42)
        vehicles = gen.generate_arrivals()
        if vehicles:
            assert vehicles[0].id == 0

    def test_reset_with_new_seed(self):
        """Resetting with a new seed should produce reproducible results."""
        gen = ArrivalGenerator(lambda_rate=3.0, seed=1)
        gen.generate_arrivals()
        gen.reset(seed=99)
        seq_a = [len(gen.generate_arrivals()) for _ in range(30)]

        gen.reset(seed=99)
        seq_b = [len(gen.generate_arrivals()) for _ in range(30)]

        assert seq_a == seq_b

    def test_reset_without_seed_keeps_rng(self):
        """Resetting without a seed should only reset the ID counter."""
        gen = ArrivalGenerator(lambda_rate=3.0, seed=42)
        gen.generate_arrivals()
        gen.reset()  # no seed
        # Just verify no exception and id restarts
        vehicles = gen.generate_arrivals()
        if vehicles:
            assert vehicles[0].id == 0
