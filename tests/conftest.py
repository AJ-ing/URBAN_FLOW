import os

import pygame

# Force headless dummy drivers for all pytest runs (CI and local headless runs)
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

# Initialize pygame display system in dummy mode once at module load time.
# This prevents 'video system not initialized' errors when loading images (e.g. in simulation.py) on headless Linux.
pygame.init()
pygame.display.set_mode((1, 1))
