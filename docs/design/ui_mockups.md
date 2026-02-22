# UrbanFlow UI Design Document

**Rushil Shandil(2024A7RM0197G)** — Pod 4: Visualization & UI

## Resources Studied before execution

Before starting the code, I looked at a bunch of existing traffic simulation projects to get ideas:

- **Mihir Gandhi's traffic sim on GitHub** — Uses pygame, single intersection. Clean look with colored rectangles for vehicles. Simple but effective layout.
- **Prit Mayani's traffic sim on GitHub** — Also pygame based. Good use of lane-based rendering. Not much in terms of UI controls though.
- **Towards Data Science pygame tutorials (Parts 1 & 3)** — Really helpful for understanding how to handle vehicle movement and signal phases in pygame.
- **SUMO traffic simulator** — Watched some YouTube demos. This is the industry standard — they use top-down view with color-coded vehicles, detailed lane markings. Took a lot of inspiration from their layout.

## Layout

I went with a 3-panel layout. The main traffic view takes up most of the screen, with a sidebar for charts and a control bar at the bottom.

```
+------------------------------+-----------+
|                              |           |
|   Traffic Network View       |  Metrics  |
|   (roads, vehicles, signals) |  Charts   |
|                              |           |
|   ~65% of width              |  ~25%     |
|                              |           |
+------------------------------+-----------+
|         Control Bar (play/pause/speed)    |
+-------------------------------------------+
```

- Default window: 1280x720
- Resizable (panels adjust automatically)
- Target: 60 FPS

## Colours

I chose a dark theme because traffic lights and coloured vehicles show up way better on dark backgrounds.

| Element | Color | Hex |
|---------|-------|-----|
| Background | Dark navy | #0f0f23 |
| Panel bg | Slightly lighter | #1a1a2e |
| Roads | Dark gray | #3c3c3c |
| Lane markings | White-ish | #dcdcdc |
| Grass | Dark green | #1e371e |
| Signal Red | Red | #dc3545 |
| Signal Green | Green | #32c850 |
| Signal Yellow | Amber | #f0c832 |
| Vehicles (north) | Blue | #4a9eff |
| Vehicles (south) | Red | #ff6b6b |
| Vehicles (east) | Yellow | #ffc107 |
| Vehicles (west) | Green | #28dc78 |
| Text | Light gray | #e0e0e0 |
| Accent | Blue | #4a9eff |

Vehicles are colour-coded by direction so you can see traffic flow at a glance.

## Controls

| Action | Keyboard | Mouse |
|--------|----------|-------|
| Play/Pause | Space | Click button |
| Reset | R | Click button |
| Step forward | Right arrow | Click button |
| Speed up/down | +/- | Drag slider |
| Zoom | - | Scroll wheel |
| Pan | - | Middle mouse drag |

## Data Interface

For integration with Pod 1 (simulation) and Pod 3 (metrics), the visualization expects data in this format:

```python
simulation_state = {
    "vehicles": [
        {"grid_x": 0.5, "grid_y": 1.0, "direction": "east"},
        ...
    ],
    "signals": [
        {"grid_x": 0, "grid_y": 0, "state": {"ns": "red", "ew": "green"}},
        ...
    ],
    "metrics": {
        "throughput": 842.0,
        "avg_wait_time": 23.4,
        "avg_queue_length": 6.2,
    }
}
```

## What's Next (Phase 2-3)

- Animate vehicles (smooth movement along roads)
- Connect to real simulation engine from Pod 1
- Live metrics from Pod 3
- Comparison view (fixed vs adaptive signals side by side)
- Better vehicle sprites maybe