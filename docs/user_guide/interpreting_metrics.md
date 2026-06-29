# Interpreting Metrics

This guide explains the performance metrics displayed on the dashboard.

## Dashboard Metrics

1. **Throughput (vph)**:
   - *Definition*: Vehicles per hour calculated over a rolling 60-second window.
   - *Formula*: `(crossed_vehicles / 60) * 3600`
   - *Interpretation*: Higher is better. A higher throughput indicates the intersection is processing vehicles efficiently.

2. **Average Wait Time (s)**:
   - *Definition*: Average time vehicles spent completely stopped before crossing the intersection.
   - *Interpretation*: Lower is better. A low wait time indicates signals are changing responsively.

3. **Average Travel Time (s)**:
   - *Definition*: Total time from spawning at the screen edge to crossing the stop line.
   - *Interpretation*: Lower is better. Measures overall delay.

4. **Queue Length**:
   - *Definition*: Sum of all stopped, uncrossed vehicles across all approaches.
   - *Interpretation*: Lower is better. Spikes indicate congestion or phase delays.

---

## Comparing Fixed vs Adaptive Controllers

To evaluate the efficiency of the adaptive rules:
1. Run a 5-minute simulation under Fixed-Time control.
2. Click **Export CSV** at the end of the run.
3. Reset and run under Adaptive control.
4. Export the second run's CSV.
5. Use the `ComparisonAnalyzer` to compute relative percentage improvements.
