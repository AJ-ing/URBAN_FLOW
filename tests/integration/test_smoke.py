import os
import sys
from pathlib import Path

# Set dummy drivers for headless CI execution
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame


def test_smoke_imports():
    """Verify that all core modules can be imported and initialized without errors."""
    pygame.init()
    assert pygame.get_init()

    import controller  # noqa: F401
    import dashboard_state  # noqa: F401
    import data_logger  # noqa: F401
    import main  # noqa: F401
    import metrics_calculator  # noqa: F401
    import renderer  # noqa: F401
    import signals
    import simulation
    import ui_theme  # noqa: F401

    assert simulation.SPAWN_INTERVAL_S > 0
    assert len(signals.signals) == 4


def test_src_main_wrapper_imports():
    """Verify that the src/main.py wrapper can be imported and points to the correct entry."""
    sys_path_backup = list(sys.path)
    cwd_backup = os.getcwd()

    src_dir = str(Path(__file__).resolve().parent.parent.parent / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    try:
        import src.main as src_main

        assert hasattr(src_main, "main")
    finally:
        sys.path = sys_path_backup
        os.chdir(cwd_backup)
