from __future__ import annotations

from pathlib import Path
from typing import Final    

import pyray as rl

# Window / visuals
WINDOW_WIDTH: Final[int] = 1920
WINDOW_HEIGHT: Final[int] = 1080
FONT_SIZE: Final[int] = 120

# Gameplay tuning (keep what you actually use)
PLAYER_SPEED: Final[float] = 500.0
LASER_SPEED: Final[float] = 600.0
METEOR_SPEED_RANGE: Final[tuple[int, int]] = (300, 400)
METEOR_TIMER_DURATION: Final[float] = 0.4

# Nice color set (raylib built-ins)

# Asset paths
ASSETS_DIR = Path(__file__).resolve().parent  # adjust if you keep assets elsewhere


def asset(*parts: str) -> str:
    """Build a path to an asset and return it as str (raylib expects str)."""
    return str(ASSETS_DIR.joinpath(*parts))
