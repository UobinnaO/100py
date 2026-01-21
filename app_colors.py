# Centralized palette for your app.
# pyray's color constants are ALREADY rl.Color objects.
# This file gives them semantic names + adds custom colors.

from __future__ import annotations

import pyray as rl
from pyray import (
    LIGHTGRAY,
    GRAY,
    DARKGRAY,
    YELLOW,
    GOLD,
    ORANGE,
    PINK,
    RED,
    MAROON,
    GREEN,
    LIME,
    DARKGREEN,
    SKYBLUE,
    BLUE,
    DARKBLUE,
    PURPLE,
    VIOLET,
    DARKPURPLE,
    BEIGE,
    BROWN,
    DARKBROWN,
    WHITE,
    BLACK,
    BLANK,
    MAGENTA,
    RAYWHITE,
)

# ------------------------------------------------------------------------------
# Semantic palette (your game’s meaning-based names)
# ------------------------------------------------------------------------------

# Background / world
BG_COLOR = WHITE
BG_COLOR_ALT = DARKPURPLE

# Player
PLAYER_COLOR = RED
PLAYER_HIT_COLOR = ORANGE

# Enemies
ENEMY_COLOR = MAROON
ENEMY_WEAK_COLOR = PINK

# UI
UI_TEXT_COLOR = RAYWHITE
UI_TEXT_MUTED = LIGHTGRAY
UI_ACCENT_COLOR = GOLD

# Debug overlays
DEBUG_TEXT_COLOR = GREEN
DEBUG_WARN_COLOR = YELLOW
DEBUG_ERROR_COLOR = MAGENTA
FRAME_COUNT_TEXT_COLOR = BLACK

# Input overlays
MOUSE_COLOR = RED
STICK_COLOR = BLUE

# Audio / recorder status
AUDIO_TEXT_COLOR = GREEN
RECORDER_TEXT_COLOR = PURPLE

# ------------------------------------------------------------------------------
# Extra custom colors (beyond Raylib's defaults)
# ------------------------------------------------------------------------------


def make_color(r: int, g: int, b: int, a: int = 255) -> rl.Color:
    """Helper to build new rl.Color objects just once at import time."""
    return rl.Color(r, g, b, a)


# Soft palette
SOFT_BLUE = make_color(80, 150, 255)
SOFT_GREEN = make_color(120, 220, 160)
SOFT_RED = make_color(255, 120, 140)
SOFT_PURPLE = make_color(180, 140, 255)

# Neon palette
NEON_CYAN = make_color(0, 255, 255)
NEON_MAGENTA = make_color(255, 0, 200)
NEON_YELLOW = make_color(255, 255, 0)

# Dark palette
DARK_TEAL = make_color(0, 60, 70)
DARK_SLATE = make_color(30, 40, 60)
DARK_VIOLET = make_color(40, 10, 70)

# Example semantic uses
HEALTH_BAR_GOOD = SOFT_GREEN
HEALTH_BAR_BAD = SOFT_RED
BULLET_COLOR = NEON_CYAN
POWERUP_COLOR = NEON_YELLOW
PORTAL_COLOR = NEON_MAGENTA
