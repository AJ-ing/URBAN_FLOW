# Requirements Traceability Matrix

This document maps each functional requirement (FR) of the UrbanFlow system to its corresponding source module and unit/integration tests.

| Requirement ID | Requirement Description | Implementation Module | Verification Test Case |
|---|---|---|---|
| **FR-SIM-01** | Spawning vehicles with correct directions | `simulation.py` | `TestVehicleSpawning` in `tests/unit/test_simulation.py` |
| **FR-SIM-02** | Spawning vehicles with random lane selections | `simulation.py` | `test_spawn_creates_vehicle_in_lane_1_or_2` |
| **FR-SIM-03** | Speed adjustment based on vehicle classes | `simulation.py` | `test_vehicle_type_affects_nominal_speed` |
| **FR-SIM-04** | Queue formation & distance gap maintenance | `simulation.py` | `TestQueueing` in `tests/unit/test_simulation.py` |
| **FR-SIM-05** | Intersection turning geometry animations | `simulation.py` | `test_vehicle_moves_forward_when_not_stopped` |
| **FR-CTL-01** | Fixed-Time pre-timed cycle phase changes | `controller.py` | `TestFixedTimeController` in `tests/unit/test_controller.py` |
| **FR-CTL-02** | Fixed-time cycle remaining countdown calculation | `controller.py` | `test_fixed_controller_time_until_green` |
| **FR-CTL-03** | Adaptive Rule: `WaitTimeThreshold` enforcement | `controller.py` | `TestWaitTimeThreshold` in `tests/unit/test_controller.py` |
| **FR-CTL-04** | Adaptive Rule: `QueueLengthExtension` activation | `controller.py` | `TestQueueLengthExtension` in `tests/unit/test_controller.py` |
| **FR-CTL-05** | Adaptive Rule: `EarlyTermination` checks | `controller.py` | `TestEarlyTermination` in `tests/unit/test_controller.py` |
| **FR-CTL-06** | Adaptive Rule: `DemandResponsiveSelection` query | `controller.py` | `TestDemandResponsiveSelection` |
| **FR-CTL-07** | Adaptive Rule: `PeakHourBoost` scaling | `controller.py` | `TestPeakHourBoost` in `tests/unit/test_controller.py` |
| **FR-CTL-08** | Adaptive Rule: `BalancedServiceGuarantee` query | `controller.py` | `TestBalancedServiceGuarantee` |
| **FR-MET-01** | Rolling throughput KPI calculation | `metrics_calculator.py` | `TestThroughput` in `tests/unit/test_metrics.py` |
| **FR-MET-02** | Mean stopped wait time accumulation | `metrics_calculator.py` | `TestAverageWaitTime` in `tests/unit/test_metrics.py` |
| **FR-MET-03** | Mean travel time accumulation | `metrics_calculator.py` | `TestAverageTravelTime` in `tests/unit/test_metrics.py` |
| **FR-MET-04** | Rolling window database pruning | `metrics_calculator.py` | `TestMetricsEdgeCases` in `tests/unit/test_metrics.py` |
| **FR-DAT-01** | Telemetry logging in memory | `data_logger.py` | `TestDataLogger` in `tests/unit/test_data_logger.py` |
| **FR-DAT-02** | Exporting logged history to CSV tables | `data_logger.py` | `TestCSVExporter` in `tests/unit/test_data_logger.py` |
| **FR-DAT-03** | Exporting runs to JSON files | `data_logger.py` | `TestJSONExporter` in `tests/unit/test_data_logger.py` |
| **FR-DAT-04** | Run comparison analyzer computations | `data_logger.py` | `TestComparisonAnalyzer` |
| **FR-UI-01** | Play/Pause dashboard toggle | `dashboard_state.py` | `TestPlaybackToggle` in `test_renderer.py` |
| **FR-UI-02** | Simulation speed slider state scaling | `dashboard_state.py` | `test_renderer.py` |
| **FR-UI-03** | Reset cycle state restoration | `dashboard_state.py` | `TestResetRequest` in `test_renderer.py` |
| **FR-UI-04** | Direct CSV export trigger validation | `dashboard_state.py` | `TestExportGating` in `test_renderer.py` |
| **FR-UI-05** | Catmull-Rom spline line chart rendering | `renderer.py` | `test_renderer.py` |
| **FR-UI-06** | Headless smoke integration test verification | `src/main.py` | `test_smoke_imports` in `tests/integration/test_smoke.py` |
