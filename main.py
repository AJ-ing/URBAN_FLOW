# Main entry point. Runs the pygame loop, handles input, ties everything together.
# Run with: python main.py

from __future__ import annotations

import asyncio
import sys
from datetime import datetime

import pygame

import signals as signals_module
import simulation
import ui_theme as T
from dashboard_state import MODE_ADAPTIVE, MODE_FIXED, DashboardState
from renderer import Renderer

# try to import pod 3's stuff. if it's missing for some reason we fall back
# to fake data so the dashboard still works for demos
try:
    from data_logger import CSVExporter, DataLogger
    from metrics_calculator import MetricsCalculator

    POD3_AVAILABLE = True
except ImportError:
    POD3_AVAILABLE = False
    print("[WARN] POD 3 metrics not available — using mock snapshots.")


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
MODE_ADAPTIVE_COLOR = (0, 200, 100)
MODE_FIXED_COLOR = (200, 180, 0)
TIME_COORDS = (1100, 50)


def get_queue_lengths() -> dict:
    # count how many vehicles are stopped (speed=0) in each direction
    # the controller uses this to decide which direction to give green to
    queues = {0: 0, 1: 0, 2: 0, 3: 0}
    for vehicle in simulation.iter_vehicles():
        if vehicle.crossed == 0 and vehicle.speed == 0:
            queues[vehicle.direction_number] += 1
    return queues


def mock_snapshot(elapsed: float) -> dict:
    # fake metrics data for when pod 3 isn't available
    # using sin/cos so the chart has some variation to show
    import math

    return {
        "throughput": 300 + 150 * math.sin(elapsed / 8),
        "avg_wait": 8 + 4 * math.sin(elapsed / 5),
        "avg_travel": 25 + 5 * math.cos(elapsed / 6),
        "queue_length": int(5 + 4 * math.sin(elapsed / 3)),
    }


async def main() -> None:
    pygame.init()

    # native size is 1760x800 (sim + sidebar)
    native_size = (T.WINDOW_WIDTH, T.WINDOW_HEIGHT)

    # we draw at native but display scaled down so it fits any laptop
    # 0.75 gives us ~1320x600 which fits comfortably everywhere
    DISPLAY_SCALE = 0.75
    display_size = (
        int(native_size[0] * DISPLAY_SCALE),
        int(native_size[1] * DISPLAY_SCALE),
    )

    # RESIZABLE lets the user drag the window bigger for sharper text
    display = pygame.display.set_mode(display_size, pygame.RESIZABLE)

    # we draw everything to this surface at full resolution
    # then scale it down to the display at the end of each frame
    screen = pygame.Surface(native_size)
    pygame.display.set_caption("UrbanFlow — Adaptive Traffic Simulation")
    clock = pygame.time.Clock()

    screen.fill(T.BG_MAIN)

    # load images once up front
    background = pygame.image.load("images/intersection.png")
    red_signal = pygame.image.load("images/signals/red.png")
    yellow_signal = pygame.image.load("images/signals/yellow.png")
    green_signal = pygame.image.load("images/signals/green.png")

    sim_font = pygame.font.Font(None, 30)
    mode_font = pygame.font.SysFont("Arial", 18, bold=True)

    # dashboard stuff
    state = DashboardState()
    renderer = Renderer()

    # metrics stuff (only if pod 3 is available)
    if POD3_AVAILABLE:
        metrics = MetricsCalculator(window_s=60)
        logger = DataLogger()
    else:
        metrics = None
        logger = None

    spawn_accumulator = 0.0
    signals_module.sync_controller_state(get_queue_lengths())

    while True:
        # real_dt = actual wall-clock time since last frame
        # at 60fps this is ~0.016s
        real_dt = clock.tick(60) / 1000.0

        # step means "advance one frame even though paused"
        do_step = state.consume_step()

        # figure out how much sim time to advance this frame
        # - playing normally: advance at real-time speed
        # - paused + step button pressed: advance one normal frame
        # - paused otherwise: don't advance at all
        if state.is_playing:
            sim_dt = real_dt
        elif do_step:
            sim_dt = real_dt
        else:
            sim_dt = 0.0

        # only spawn new vehicles when time is actually moving
        if sim_dt > 0:
            state.elapsed_sim_time += sim_dt
            spawn_accumulator += sim_dt
            # catch up safely if a long frame spans multiple spawn intervals
            while spawn_accumulator >= simulation.SPAWN_INTERVAL_S:
                simulation.generate_vehicle()
                spawn_accumulator -= simulation.SPAWN_INTERVAL_S

        # --- figure out where the mouse is in sim-space ---
        # pygame reports mouse in window coords but our sim is at a different
        # resolution. so we scale the mouse pos to match our native coords
        raw_mouse = pygame.mouse.get_pos()
        ds = display.get_size()
        mouse_pos = (
            int(raw_mouse[0] * native_size[0] / ds[0]),
            int(raw_mouse[1] * native_size[1] / ds[1]),
        )

        # --- event handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                _shutdown(state, logger)
                return

            # keyboard shortcuts
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    state.toggle_play()
                elif event.key == pygame.K_RIGHT:
                    state.request_step()
                elif event.key == pygame.K_r:
                    state.request_reset()
                elif event.key == pygame.K_a:
                    # A = switch to adaptive
                    state.set_mode(MODE_ADAPTIVE)
                    signals_module.set_controller_mode("adaptive", get_queue_lengths())
                elif event.key == pygame.K_f:
                    # F = switch to fixed-time
                    state.set_mode(MODE_FIXED)
                    signals_module.set_controller_mode("fixed", get_queue_lengths())
                elif event.key == pygame.K_e:
                    state.request_export()

            # mouse clicks
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                btn = renderer.hit_test_button(mouse_pos)
                if btn:
                    _handle_button(btn, state)

        # --- handle reset request ---
        if state.consume_reset():
            signals_module.active_controller.reset()
            signals_module.sync_controller_state(get_queue_lengths())
            # sim might have a reset function, use it if it exists
            (
                simulation.reset_vehicles()
                if hasattr(simulation, "reset_vehicles")
                else None
            )
            state.elapsed_sim_time = 0.0
            spawn_accumulator = 0.0
            # fresh metrics calculator so the numbers start from zero
            if metrics is not None:
                metrics = MetricsCalculator(window_s=60)
            print("[RESET] simulation cleared")

        # --- update signals ---
        queues = get_queue_lengths()
        if sim_dt > 0:
            signals_module.update_signals_tick(sim_dt, queues)

        # --- update metrics ---
        if POD3_AVAILABLE and metrics is not None:
            # POD3 metrics are available - use real metrics
            metrics.update(
                sim_dt,
                list(simulation.iter_vehicles()),
                queues,
            )
            snap = metrics.get_snapshot()
        else:
            # POD3 not available - use mock data for demo
            snap = mock_snapshot(state.elapsed_sim_time)

        state.update_snapshot(snap, state.elapsed_sim_time)

        # log data for CSV export (silently ignore errors so we don't spam)
        if logger is not None:
            try:
                logger.log(snap, state.elapsed_sim_time)
            except Exception:
                pass

        # --- export button pressed? ---
        if state.consume_export() and POD3_AVAILABLE and logger is not None:
            # timestamp in filename so we don't overwrite previous exports
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"urbanflow_export_{ts}.csv"
            try:
                CSVExporter.export(logger, path)
                state.last_export_path = path
                print(f"[EXPORT] saved {path}")
            except Exception as e:
                print(f"[EXPORT] failed: {e}")

        # --- draw everything ---
        screen.fill(T.BG_MAIN)
        screen.blit(background, (0, 0))

        # signals - green/yellow/red based on which direction has priority
        for index in range(signals_module.noOfSignals):
            if index == signals_module.currentGreen:
                if signals_module.currentYellow == 1:
                    screen.blit(yellow_signal, signals_module.signalCoods[index])
                else:
                    screen.blit(green_signal, signals_module.signalCoods[index])
            else:
                screen.blit(red_signal, signals_module.signalCoods[index])

        # countdown timer above each signal
        for index, signal in enumerate(signals_module.signals):
            sig_surf = sim_font.render(str(signal.signalText), True, WHITE, BLACK)
            screen.blit(sig_surf, signals_module.signalTimerCoods[index])

        # vehicles-crossed counter for each direction
        crossed_counts = simulation.get_crossed_counts()
        for index in range(signals_module.noOfSignals):
            count_surface = sim_font.render(
                str(crossed_counts[index]), True, BLACK, WHITE
            )
            screen.blit(count_surface, signals_module.vehicleCountCoods[index])

        # small mode label in top-left of sim
        mode_text = "Mode: " + signals_module.controller_mode.upper()
        mode_color = (
            MODE_ADAPTIVE_COLOR
            if signals_module.controller_mode == "adaptive"
            else MODE_FIXED_COLOR
        )
        mode_surface = mode_font.render(mode_text, True, mode_color)
        screen.blit(mode_surface, (10, 10))

        # draw vehicles + advance their position (only if time is moving)
        for vehicle in simulation.iter_vehicles():
            screen.blit(vehicle.image, [vehicle.x, vehicle.y])
            if sim_dt > 0:
                vehicle.move()

        # then the dashboard on top
        renderer.draw_dashboard(screen, state, mouse_pos)

        # finally scale our native-size surface down to the actual window size
        pygame.transform.smoothscale(screen, display.get_size(), display)
        pygame.display.update()
        await asyncio.sleep(0)

        # auto-stop at 300s
        if state.elapsed_sim_time >= simulation.SIMULATION_TIME_S:
            simulation.show_stats(state.elapsed_sim_time)
            _shutdown(state, logger)
            return


def _handle_button(key: str, state: DashboardState) -> None:
    # dispatch a button click to the right action
    if key == "play":
        state.play()
    elif key == "pause":
        state.pause()
    elif key == "step":
        state.request_step()
    elif key == "reset":
        state.request_reset()
    elif key == "mode_fixed":
        state.set_mode(MODE_FIXED)
        signals_module.set_controller_mode("fixed", get_queue_lengths())
    elif key == "mode_adaptive":
        state.set_mode(MODE_ADAPTIVE)
        signals_module.set_controller_mode("adaptive", get_queue_lengths())
    elif key == "export":
        state.request_export()


def _shutdown(state: DashboardState, logger) -> None:
    # auto-export on quit if user collected data but didn't manually export
    # (so they don't lose their data by forgetting to click the button)
    if logger is not None and state.export_enabled:
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"urbanflow_autoexport_{ts}.csv"
            CSVExporter.export(logger, path)
            print(f"[AUTO-EXPORT] {path}")
        except Exception:
            pass
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    asyncio.run(main())
