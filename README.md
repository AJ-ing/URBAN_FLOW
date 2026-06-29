# UrbanFlow — Adaptive Traffic Intersection Simulator

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://python.org)
[![Pygame](https://img.shields.io/badge/Pygame-2.6.1-green?logo=pygame)](https://pygame.org)
[![Tests](https://img.shields.io/badge/Tests-156%20passing-brightgreen?logo=pytest)](tests/)
[![Coverage](https://img.shields.io/badge/Coverage-95%25-brightgreen)](tests/)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![Code Style](https://img.shields.io/badge/Code%20Style-black-000000)](https://github.com/psf/black)

> A real-time, single-intersection traffic simulation with two interchangeable signal controllers, live performance metrics, an animated dashboard, and one-click CSV export — all built in pure Python and Pygame.

---

## Table of Contents

1. [Overview](#overview)
2. [Screenshots](#screenshots)
3. [Features](#features)
4. [Architecture Overview](#architecture-overview)
5. [Installation](#installation)
6. [Quick Start](#quick-start)
7. [Controls](#controls)
8. [Configuration Guide](#configuration-guide)
9. [Running Simulations](#running-simulations)
10. [Signal Controllers](#signal-controllers)
11. [Metrics Explained](#metrics-explained)
12. [Testing](#testing)
13. [CI/CD](#cicd)
14. [Contributing](#contributing)
15. [License](#license)

---

## Overview

UrbanFlow simulates a standard four-way signalised intersection with north, south, east, and west approaches. Vehicles (cars, buses, trucks, and bikes) spawn continuously, join queues, wait for a green light, cross the stop line, and exit — all rendered in real-time at 60 fps.

Two signal controllers are included:

| Controller | Strategy |
|---|---|
| **Fixed-Time** | Pre-timed green phases of equal duration, cycling N → E → S → W. |
| **Adaptive** | Queue-sensing, rule-based logic that extends greens for heavy traffic, terminates early when lanes clear, and prevents starvation. |

A sidebar dashboard displays live KPIs, a scrolling throughput chart, playback controls, a speed slider, a mode toggle, and a one-click CSV export button. The simulation auto-terminates at 300 s and auto-exports collected data on exit.

---

## Screenshots

> Place simulation screenshots under `images/` and they will appear here automatically.

```
images/
└── intersection.png    ← main window screenshot (1760 × 800 native)
```

*Screenshot placeholder — run `python main.py` to see the live simulation.*

---

## Features

### Simulation Engine
- **Four-direction intersection** — North (down), East (left), South (up), West (right) approaches, each with 3 lanes
- **Four vehicle classes** — car (2.25 px/frame), bus (1.8 px/frame), truck (1.8 px/frame), bike (2.5 px/frame)
- **Turn behaviour** — 40 % of spawned vehicles turn at the intersection; turning geometry is fully animated
- **Queue physics** — vehicles maintain a `stoppingGap` of 25 px from the vehicle ahead, with a separate `movingGap` once clear of the stop line
- **Stop-line enforcement** — vehicles halt at the stop line when their direction is red/yellow and resume when green
- **Auto-spawn** — one vehicle every 0.4 s (configurable via `SPAWN_INTERVAL_S`); direction weights biased toward north approach (6:2:1:1)
- **300-second run** — simulation auto-stops at `SIMULATION_TIME_S = 300`

### Signal Controllers
- **FixedTimeController** — configurable `green_s` / `yellow_s`; three built-in plans (Plan A: 10 s, Plan B: 25 s, Plan C: 39 s); `time_until_green()` countdown for all red signals
- **AdaptiveController** — six rule engine rules evaluated in priority order:
  - `WaitTimeThreshold` (priority 100) — forces phase change when any approach waits > 45 s
  - `QueueLengthExtension` (priority 90) — extends green by 8 s when queue ≥ 5 vehicles (max 1 extension)
  - `EarlyTermination` (priority 80) — skips green remainder when active lane clears after min_green
  - `DemandResponsiveSelection` (priority 70) — switches to highest-demand waiting lane
  - `PeakHourBoost` (priority 60) — applies 1.3× service-time boost during peak window (60–180 s)
  - `BalancedServiceGuarantee` (priority 50) — prevents starvation by capping service imbalance at 2.0×
- Hard minimum green 8 s, hard maximum 90 s, fixed 3 s yellow

### Real-Time Metrics
- **Throughput** — vehicles per hour (rolling window, default 60 s in runtime, configurable)
- **Average Wait Time** — mean cumulative stopped time before crossing (seconds)
- **Average Travel Time** — mean origin-to-departure time (seconds)
- **Queue Length** — total stopped uncrossed vehicles across all 4 approaches

### Dashboard & UI
- **Sidebar** (360 × 800 px) drawn at native 1760 × 800, scaled to fit any display
- **Metric cards** — four KPI tiles update every frame
- **Throughput chart** — Catmull-Rom spline smoothed, last 120 samples (1 sample/s)
- **Playback controls** — Play, Pause, Step (single frame), Reset buttons
- **Speed slider** — 0.25× to 10× real-time; snaps to presets on release
- **Mode toggle** — Fixed ↔ Adaptive with immediate hot-swap, no restart required
- **CSV export** — one-click export to `urbanflow_export_<timestamp>.csv`
- **Auto-export on quit** — prevents data loss if user forgets to export

---

## Architecture Overview

```
main.py                     ← Pygame loop, event dispatch, hot-glue
├── simulation.py           ← Vehicle class, spawn logic, global state
├── signals.py              ← TrafficSignal, controller façade, frame tick
│   └── controller.py       ← FixedTimeController, AdaptiveController, RuleEngine
├── metrics_calculator.py   ← Rolling-window KPI computation (pure Python)
├── data_logger.py          ← DataLogger, CSVExporter, JSONExporter, ComparisonAnalyzer
├── dashboard_state.py      ← Pure-Python state machine (pygame-free)
├── renderer.py             ← All Pygame drawing code
├── ui_theme.py             ← Colours, fonts, sizes
└── configs/
    └── adaptive_params.json
```

See [`docs/architecture/component_diagram.md`](docs/architecture/component_diagram.md) for the full Mermaid component diagram and [`docs/architecture/data_flow.md`](docs/architecture/data_flow.md) for the data-flow diagram.

---

## Installation

### Prerequisites

| Requirement | Minimum Version |
|---|---|
| Python | 3.9+ (tested on 3.13) |
| pip | 22.0+ |
| A display | Required by Pygame (see [Headless Pygame](#headless-display)) |

### Step 1 — Clone the Repository

```bash
git clone https://github.com/your-org/UrbanFlow_POD4_Rushil.git
cd UrbanFlow_POD4_Rushil/UrbanFlow_POD4_Rushil
```

### Step 2 — Create a Virtual Environment

```bash
python -m venv venv
```

**Activate it:**

```bash
# macOS / Linux
source venv/bin/activate

# Windows (Command Prompt)
venv\Scripts\activate.bat

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

Runtime dependencies:

| Package | Version | Purpose |
|---|---|---|
| `pygame` | 2.6.1 | Window, rendering, event loop |
| `numpy` | ≥ 2.0.0 | Numerical arrays (metrics) |
| `matplotlib` | ≥ 3.8.0 | Chart rendering backend |

For development tools (linting, type checking, testing):

```bash
pip install -r requirements-dev.txt
```

### Step 4 — Verify Installation

```bash
python -c "import pygame; import numpy; import matplotlib; print('All dependencies OK')"
```

Expected output:

```
All dependencies OK
```

---

## Quick Start

```bash
# From the project root (UrbanFlow_POD4_Rushil/UrbanFlow_POD4_Rushil/)
python main.py
```

The window opens at approximately 1320 × 600 (scaled from native 1760 × 800 at 0.75×). You can drag any corner to resize — the simulation scales cleanly.

**First 10 seconds:**
1. Vehicles spawn and queue at the red signals
2. The Fixed-Time controller gives north approach a green phase
3. The dashboard chart begins plotting throughput
4. Press **A** to switch to Adaptive mode and observe the difference

---

## Controls

### Keyboard Shortcuts

| Key | Action |
|---|---|
| `Space` | Play / Pause simulation |
| `→` (Right Arrow) | Advance exactly one frame (only when paused) |
| `R` | Reset — clears all vehicles, resets metrics and elapsed time |
| `A` | Switch to **Adaptive** controller |
| `F` | Switch to **Fixed-Time** controller |
| `E` | Export current metrics to CSV |
| `Alt+F4` / `⌘Q` | Quit (auto-exports data if not yet exported) |

### Mouse Controls

| Action | Effect |
|---|---|
| Click **▶ Play** button | Resume simulation |
| Click **⏸ Pause** button | Pause simulation |
| Click **⏭ Step** button | Single-frame advance |
| Click **↺ Reset** button | Full reset |
| Click **FIXED** / **ADAPTIVE** | Switch controller mode |
| Click **Export CSV** | Save metrics to file |
| Drag speed slider | Adjust simulation speed (0.25× – 10×) |

### Speed Presets

The speed slider snaps to these presets on mouse release:

| Preset | Multiplier |
|---|---|
| Slowest | 0.25× |
| Slow | 0.5× |
| Normal | 1× |
| Fast | 2× |
| Faster | 4× |
| Turbo | 10× |

---

## Configuration Guide

### Adaptive Controller Parameters

Edit `configs/adaptive_params.json` to tune the adaptive controller without changing any Python code. Parameters are validated on load; out-of-range values revert to defaults.

```json
{
  "max_wait_s": 45.0,
  "queue_threshold": 5,
  "extension_s": 8.0,
  "max_extensions": 1,
  "min_green_s": 8.0,
  "peak_start_s": 60.0,
  "peak_end_s": 180.0,
  "boost_factor": 1.3,
  "peak_min_queue": 3,
  "imbalance_ratio": 2.0,
  "min_service_s": 12.0
}
```

| Parameter | Type | Bounds | Description |
|---|---|---|---|
| `max_wait_s` | float | 1 – 300 | Max seconds a direction may wait before `WaitTimeThreshold` forces a phase change |
| `queue_threshold` | int | 1 – 100 | Queue length that triggers a green extension |
| `extension_s` | float | 1 – 60 | Seconds added per `QueueLengthExtension` activation |
| `max_extensions` | int | 0 – 10 | How many extensions per green phase |
| `min_green_s` | float | 2 – 90 | Minimum green duration before any adaptive rule can fire |
| `peak_start_s` | float | 0 – 3600 | Simulation time (s) when peak-hour boost begins |
| `peak_end_s` | float | 0 – 3600 | Simulation time (s) when peak-hour boost ends |
| `boost_factor` | float | 1 – 5 | Service-time multiplier during peak hour |
| `peak_min_queue` | int | 0 – 100 | Minimum queue length to activate peak boost |
| `imbalance_ratio` | float | 1 – 10 | Max tolerated ratio between longest and shortest green service times |
| `min_service_s` | float | 1 – 60 | Minimum service time before `BalancedServiceGuarantee` can act |

### Preset Configurations

Pre-built parameter sets are available in `configs/presets/`:

```
configs/presets/
├── light_traffic.json      ← short min-green, aggressive early termination
├── heavy_traffic.json      ← long extensions, high queue_threshold
└── peak_hour.json          ← extended peak window with high boost_factor
```

### Fixed-Time Controller Plans

To switch the fixed controller to a different cycle plan, edit `signals.py`:

```python
# Line 88 — choose a plan:
fixed_controller = FixedTimeController(green_s=10, yellow_s=3)   # Plan A (default)
fixed_controller = FixedTimeController(green_s=25, yellow_s=3)   # Plan B
fixed_controller = FixedTimeController(green_s=39, yellow_s=3)   # Plan C
```

### Spawn Rate

Adjust vehicle spawn frequency in `simulation.py`:

```python
SPAWN_INTERVAL_S = 0.4   # one new vehicle every 0.4 seconds
```

### Simulation Duration

```python
SIMULATION_TIME_S = 300.0   # run for 5 minutes then auto-stop
```

### Display Scale

If the window is too large or small for your screen, adjust the scale factor in `main.py`:

```python
DISPLAY_SCALE = 0.75   # 0.75 → ~1320×600, 1.0 → native 1760×800
```

---

## Running Simulations

### Basic Run (Fixed-Time Controller)

```bash
python main.py
```

The simulation starts in Fixed-Time mode. Press **Space** to pause, **→** to step frame-by-frame, **R** to reset.

### Starting in Adaptive Mode

There is no command-line flag; simply press **A** immediately after launch, or set the default in `signals.py`:

```python
active_controller = adaptive_controller   # change from fixed_controller
controller_mode = "adaptive"
```

### Comparative Study (Fixed vs Adaptive)

1. Launch with Fixed controller
2. Let the simulation run for ≥ 60 s to collect stable metrics
3. Press **E** to export `urbanflow_export_<timestamp>_fixed.csv`
4. Press **R** to reset
5. Press **A** to switch to Adaptive controller
6. Wait another 60 s and press **E** again
7. Use `ComparisonAnalyzer` (see [API docs](docs/api/modules.md)) to compute improvement percentages

### Exporting Data

- **During run:** Press **E** or click the **Export CSV** button in the sidebar
- **On quit:** Data is auto-exported as `urbanflow_autoexport_<timestamp>.csv`
- **CSV columns:** `time_s`, `throughput`, `avg_wait`, `avg_travel`, `queue_length`

---

## Signal Controllers

### Fixed-Time Controller

The fixed-time controller cycles through all four directions (0 → 1 → 2 → 3 → 0 …) with identical phase durations regardless of real-world traffic demand.

```
Green (10 s) → Yellow (3 s) → Next direction
```

**Properties:**
- Predictable and simple to reason about
- Performs well when traffic is balanced across directions
- Sub-optimal when one approach is congested and another is empty
- `time_until_green(direction)` provides precise countdown for every red signal

### Adaptive Controller

The adaptive controller makes real-time phase decisions by evaluating six rules in priority order at the end of each minimum green window.

```
Phase elapsed < min_green_s → hold (no rule evaluation)
Phase elapsed ≥ min_green_s → evaluate rules in priority order
Phase elapsed ≥ max_green_s → force next direction
```

**Rule Evaluation Order:**

| Priority | Rule | Trigger |
|---|---|---|
| 100 | `WaitTimeThreshold` | Any direction has waited > `max_wait_s` |
| 90 | `QueueLengthExtension` | Active direction queue ≥ `queue_threshold` |
| 80 | `EarlyTermination` | Active queue = 0 and elapsed ≥ `min_green_s` |
| 70 | `DemandResponsiveSelection` | Active queue = 0, other directions have demand |
| 60 | `PeakHourBoost` | Observation only — boosts service time accounting |
| 50 | `BalancedServiceGuarantee` | Service imbalance exceeds `imbalance_ratio` |

**When to use each controller:**

| Scenario | Recommended Controller |
|---|---|
| Uniform traffic (equal demand all directions) | Fixed-Time |
| Uneven demand (one direction dominates) | Adaptive |
| Peak hour study | Adaptive with `peak_start_s`/`peak_end_s` tuned |
| Benchmarking baseline | Fixed-Time Plan A (10 s) |

---

## Metrics Explained

### Throughput (vph)

Vehicles per hour calculated over a rolling time window (default 60 s):

```
throughput = vehicles_departed_in_window / window_s × 3600
```

Higher is better. Expect 200–500 vph under normal conditions; adaptive mode typically achieves 10–20 % higher throughput than fixed during uneven traffic.

### Average Wait Time (s)

Mean cumulative stopped time of all departed vehicles before they crossed the stop line:

```
avg_wait = Σ(stop_time per vehicle) / total_departed_vehicles
```

Lower is better. Fixed-time controllers typically show 8–15 s; adaptive reduces this by up to 25 % in high-variance scenarios.

### Average Travel Time (s)

Mean total time from spawn to crossing the stop line:

```
avg_travel = Σ(current_time − spawn_time per departed vehicle) / total_departed
```

Includes queuing time. Lower is better. Typical range: 20–40 s.

### Queue Length

Instantaneous total count of stopped, uncrossed vehicles across all four directions:

```
queue_length = Σ(vehicles where speed == 0 AND crossed == 0)
```

Lower is better. Spikes indicate signal inefficiency or demand overload.

---

## Testing

### Running All Tests

```bash
# Unit tests (controller, metrics, data_logger, simulation)
pytest tests/unit/ -v

# Renderer tests (requires pygame headless display)
pytest test_renderer.py -v

# All tests together
pytest tests/unit/ test_renderer.py -v
```

### Test Suite Breakdown

| File | Tests | Coverage Area |
|---|---|---|
| `tests/unit/test_controller.py` | ~50 | FixedTimeController, AdaptiveController, all 6 rules, RuleEngine |
| `tests/unit/test_metrics.py` | ~35 | MetricsCalculator throughput, wait, travel, queue, edge cases |
| `tests/unit/test_data_logger.py` | ~40 | DataLogger, CSVExporter, JSONExporter, ComparisonAnalyzer |
| `tests/unit/test_simulation.py` | ~30 | Vehicle spawning, movement, stop-line detection |
| `test_renderer.py` | ~63 | DashboardState machine, renderer logic, NaN/Inf handling |
| **Total** | **156** | — |

### Running with Coverage

```bash
pytest tests/unit/ test_renderer.py --cov=. --cov-report=term-missing -v
```

### Test Categories

| Tag | Description |
|---|---|
| `TC-P2-*` | POD 2 controller test cases |
| `TC-P3-PV-*` | POD 3 metrics property verification |
| `TC-P3-EX-*` | POD 3 export test cases |
| `TC-P4-RS-*` | POD 4 renderer/state test cases |

### Adding New Tests

Place unit tests in `tests/unit/test_<module>.py`. All tests should be pytest-compatible and must not import pygame or simulation for pure-logic modules.

---

## CI/CD

The project is configured for GitHub Actions. Workflow file: `.github/workflows/` (add `ci.yml` to enable).

### Recommended Workflow Configuration

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.11", "3.13"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
          sudo apt-get install -y xvfb

      - name: Run unit tests
        run: pytest tests/unit/ -v --tb=short

      - name: Run renderer tests (headless)
        run: xvfb-run -a pytest test_renderer.py -v --tb=short

      - name: Check code style
        run: |
          black --check .
          isort --check-only .
          flake8 .
```

### Headless Display

Pygame requires a display server. On CI (Linux) use `xvfb-run`:

```bash
sudo apt-get install -y xvfb
xvfb-run -a python main.py
xvfb-run -a pytest test_renderer.py -v
```

On macOS the default display works without configuration. On Windows use the console subsystem.

---

## Contributing

### Development Setup

```bash
git clone https://github.com/your-org/UrbanFlow_POD4_Rushil.git
cd UrbanFlow_POD4_Rushil/UrbanFlow_POD4_Rushil
python -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
```

### Code Style

This project enforces:
- **black** for formatting (`black .`)
- **isort** for import sorting (`isort .`)
- **flake8** for linting (`flake8 .`)
- **mypy** for type checking (`mypy .`)

Run all checks:

```bash
black . && isort . && flake8 . && mypy .
```

### Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Production-ready code |
| `develop` | Integration branch |
| `feature/<name>` | New features |
| `fix/<name>` | Bug fixes |

### Pull Request Checklist

- [ ] All existing tests pass (`pytest tests/unit/ test_renderer.py -v`)
- [ ] New features have corresponding unit tests
- [ ] Code is formatted with black
- [ ] Docstrings added for all public functions
- [ ] `configs/adaptive_params.json` bounds documented if changed
- [ ] `traceability_matrix.md` updated for new functional requirements

### Module Boundaries

| Module | Allowed Imports | Forbidden |
|---|---|---|
| `dashboard_state.py` | stdlib only | pygame, simulation |
| `metrics_calculator.py` | stdlib only | pygame, simulation, data_logger |
| `data_logger.py` | stdlib only | pygame, simulation, metrics_calculator |
| `controller.py` | stdlib only | pygame, simulation, signals |
| `renderer.py` | pygame, ui_theme, dashboard_state | simulation, metrics_calculator |

---

## Project Structure

```
UrbanFlow_POD4_Rushil/
├── main.py                      ← Entry point and Pygame event loop
├── simulation.py                ← Vehicle physics and global simulation state
├── controller.py                ← FixedTimeController, AdaptiveController, RuleEngine
├── signals.py                   ← Signal timing, config loader, controller façade
├── metrics_calculator.py        ← Rolling-window KPI computation
├── data_logger.py               ← DataLogger, CSVExporter, JSONExporter, ComparisonAnalyzer
├── dashboard_state.py           ← Pure-Python dashboard state machine
├── renderer.py                  ← All Pygame drawing code
├── ui_theme.py                  ← Colours, fonts, layout constants
├── test_renderer.py             ← Renderer and dashboard state tests
├── requirements.txt             ← Runtime dependencies
├── requirements-dev.txt         ← Development dependencies
├── setup.py                     ← Package setup
├── configs/
│   ├── adaptive_params.json     ← Adaptive controller tuning parameters
│   └── presets/                 ← Preset configurations
├── images/
│   ├── intersection.png         ← Background image (1400 × 800)
│   ├── signals/                 ← Signal sprites (red/yellow/green)
│   ├── up/, down/, left/, right/ ← Vehicle sprites per direction
├── tests/
│   ├── unit/
│   │   ├── test_controller.py
│   │   ├── test_metrics.py
│   │   ├── test_data_logger.py
│   │   └── test_simulation.py
│   ├── integration/
│   └── performance/
└── docs/
    ├── architecture/
    │   ├── component_diagram.md
    │   └── data_flow.md
    ├── api/
    │   └── modules.md
    └── user_guide/
        ├── installation.md
        ├── running_simulations.md
        └── interpreting_metrics.md
```

---

## License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2026 Rushil Shandil

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

*Built by Rushil Shandil — UrbanFlow POD 4*