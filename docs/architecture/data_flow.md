# Data Flow Diagram

This document illustrates how data flows throughout the UrbanFlow system during a single frame update.

## Real-Time Frame Update Flow

```mermaid
sequenceDiagram
    participant Main as main.py
    participant Sim as simulation.py
    participant Controller as controller.py / signals.py
    participant Metrics as metrics_calculator.py
    participant Logger as data_logger.py
    participant Dash as dashboard_state.py
    participant Renderer as renderer.py

    loop Every Frame
        Main->>Sim: Update Vehicle physics (move)
        Main->>Sim: Calculate queue lengths per approach
        Sim-->>Main: Return queues dict
        
        Main->>Controller: update_signals_tick(dt, queues)
        Controller->>Controller: Evaluate Rules
        Controller-->>Main: Return active signal states & remaining durations
        
        Main->>Metrics: update(dt, live_vehicles, queues)
        Metrics->>Metrics: Prune stale entries & compute averages (wait/travel/throughput)
        Metrics-->>Main: Return metrics snapshot dict
        
        Main->>Logger: log(snapshot, elapsed_time)
        Main->>Dash: update_snapshot(snapshot, elapsed_time)
        
        Main->>Renderer: draw_dashboard(screen, state, mouse_pos)
        Renderer->>Renderer: Draw live metrics, throughput line charts, playback buttons
    end
```

---

## Key Pipelines

1. **Simulation State to Metrics**:
   - `simulation.py` maintains the collection of active vehicle objects.
   - On every tick, `main.py` extracts a list of live vehicles and a dictionary of queue counts (number of stopped vehicles behind the stop-lines).
   - This information is fed to `MetricsCalculator.update()`, which tracks birth/crossing milestones.

2. **Controller Decisions to Signals**:
   - Queue sizes are sent to `signals.py` which passes them to the active controller.
   - The adaptive controller evaluates rules sequentially. The resulting light configurations are propagated back to the module-level state in `signals.py` and applied to the Pygame visualization.

3. **Snapshots to Dashboard**:
   - The aggregated KPI dictionary is consumed by `DashboardState` to maintain sample buffers.
   - The rendering surface reads the values and paints the sidebar widgets.

4. **Persistence & Export**:
   - Snapshots are logged to `DataLogger.records` in memory.
   - Clicking "Export CSV" or quitting the app triggers `CSVExporter.export()`, which validates paths against path traversal vulnerabilities and writes rows.
