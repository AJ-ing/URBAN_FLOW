# Architecture Component Diagram

This document contains a Mermaid component diagram showing the module boundaries and relationships within the UrbanFlow system.

```mermaid
graph TD
    %% Styling
    classDef core fill:#264664,stroke:#00D4AA,color:#E8F4F8;
    classDef ui fill:#112233,stroke:#FFC000,color:#E8F4F8;
    classDef config fill:#0d1b2a,stroke:#a4bccc,color:#E8F4F8;
    
    %% Components
    main[main.py: Game Loop & Event Dispatch]:::ui
    renderer[renderer.py: Pygame Drawing UI]:::ui
    dashboard_state[dashboard_state.py: UI State Machine]:::ui
    
    simulation[simulation.py: Physics Engine & Vehicle Spawning]:::core
    signals[signals.py: Timing & Controller Façade]:::core
    controller[controller.py: Rule-Engine, Fixed & Adaptive Controllers]:::core
    metrics_calculator[metrics_calculator.py: Real-Time Metrics Analytics]:::core
    data_logger[data_logger.py: Persistence Pipeline & CSV/JSON Export]:::core
    
    config_file[(configs/adaptive_params.json)]:::config
    
    %% Relationships
    main --> simulation
    main --> signals
    main --> renderer
    main --> dashboard_state
    
    renderer --> dashboard_state
    
    signals --> controller
    signals --> simulation
    signals --> config_file
    
    simulation --> simulation_pycache[__pycache__]
    
    main --> metrics_calculator
    main --> data_logger
    
    metrics_calculator --> simulation
    data_logger --> metrics_calculator
```

---

## Component Responsibilities

1. **`main.py` (Game Loop)**: Ticks the clocks, polls keyboard/mouse events, updates the active signal controller, updates metrics, invokes the renderer, and handles clean shutdowns/auto-exports.
2. **`simulation.py` (Physics)**: Manages vehicle positions, vehicle queuing distance checks, speed state updates, turning geometry rotations, stop line checks, and active vehicle sprite pools.
3. **`signals.py` (Façade)**: Loads parameters, validates ranges, exposes the current green/yellow active light states to renderer, and manages timing countdown calculations.
4. **`controller.py` (Rules)**: Houses the logic for `FixedTimeController` and `AdaptiveController` (the prioritized rule evaluation engine evaluating `WaitTimeThreshold`, `QueueLengthExtension`, `EarlyTermination`, etc.).
5. **`metrics_calculator.py` (Analytics)**: Pure Python engine checking rolled wait/travel/queue metrics in a sliding time window.
6. **`data_logger.py` (Persistence)**: Handles formatting of snapshots to CSV/JSON tables, secure path validation, and computes improvement percentages.
