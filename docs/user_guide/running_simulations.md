# Running Simulations

Learn how to control, configure, and analyze traffic scenarios in the simulator.

## Launching the Simulator

To launch the simulator from the repository root:
```bash
python src/main.py
```

---

## Interactive Controls

### Keyboard Bindings

- **`Space`**: Toggle Play/Pause playback state.
- **`Right Arrow (→)`**: Step forward by exactly one frame (only works when paused).
- **`R`**: Reset simulation (wipes vehicles and starts timers from zero).
- **`A`**: Hot-swap to the **Adaptive** Controller.
- **`F`**: Hot-swap to the **Fixed-Time** Controller.
- **`E`**: Trigger CSV export of current metrics logs.

### Mouse Interactions

- **Speed Slider**: Click and drag the speed handle on the sidebar to adjust speed from `0.25x` to `10.0x`.
- **Mode Toggle Buttons**: Tap the **Fixed** or **Adaptive** button on the sidebar to change controllers on the fly.
- **Export Button**: Tap the **Export CSV** button to save reports.
- **Playback Icons**: Use the Play, Pause, Step, and Reset buttons below the timer.
