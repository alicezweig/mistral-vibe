"""Constants for the pets module.

This module provides all reusable constants for the pets functionality,
including frame dimensions, image protocol settings, and CDN configuration.
"""
from __future__ import annotations

from vibe.cli.textual_ui.pets.models import Animation

# --- Frame Dimensions ---

DEFAULT_FRAME_WIDTH = 192
DEFAULT_FRAME_HEIGHT = 208
DEFAULT_FRAME_COLUMNS = 8
DEFAULT_FRAME_ROWS = 9

# Calculated from defaults
SPRITESHEET_WIDTH = DEFAULT_FRAME_COLUMNS * DEFAULT_FRAME_WIDTH  # 1536
SPRITESHEET_HEIGHT = DEFAULT_FRAME_ROWS * DEFAULT_FRAME_HEIGHT  # 1872

# --- Pet Pack Configuration ---

PET_CDN_BASE_URL = "https://persistent.oaistatic.com/codex/pets/v1"
PET_PACK_VERSION = "v1"
PET_PACK_DIR = "cache/pets"

# --- Pet IDs ---

BUILTIN_PETS = [
    "codex",
    "dewey",
    "fireball",
    "rocky",
    "seedy",
    "stacky",
    "bsod",
    "null-signal",
]

DEFAULT_PET_ID = "codex"
DISABLED_PET_ID = "disabled"
CUSTOM_PET_PREFIX = "custom:"

# --- Maximum Limits ---

MAX_PET_FRAMES = 256
MAX_ANIMATION_FPS = 60.0

# --- Image Protocol ---

KITTY_IMAGE_ID = 0xC0DE  # Fixed image ID for Kitty protocol
PET_IMAGE_ID = KITTY_IMAGE_ID  # Alias for consistency
PET_TARGET_HEIGHT_PX = 75  # Target display height in pixels

# --- Display Layout ---

TERMINAL_ROW_HEIGHT_PX = 15
PET_COMPOSER_GAP_PX = 10

# --- Default Animations ---
# These match the Codex spritesheet layout (8x9 grid)
# Row 0: frames 0-7    -> idle
# Row 1: frames 8-15   -> running-right
# Row 2: frames 16-23  -> running-left
# Row 3: frames 24-31  -> waving
# Row 4: frames 32-39  -> jumping
# Row 5: frames 40-47  -> failed
# Row 6: frames 48-55  -> waiting
# Row 7: frames 56-63  -> running
# Row 8: frames 64-71  -> review

DEFAULT_ANIMATIONS: dict[str, Animation] = {
    "idle": Animation(
        frames=[0, 1, 2, 3, 4, 5], fps=8.0, loop=True, fallback="idle", loop_start=0
    ),
    "running": Animation(
        # Use row 7 (frames 56-63) for running animation
        frames=[56, 57, 58, 59, 60, 61, 62, 63],
        fps=10.0,
        loop=True,
        fallback="idle",
        loop_start=0,
    ),
    "running-right": Animation(
        # Row 1: frames 8-15
        frames=[8, 9, 10, 11, 12, 13, 14, 15],
        fps=10.0,
        loop=True,
        fallback="idle",
        loop_start=0,
    ),
    "running-left": Animation(
        # Row 2: frames 16-23
        frames=[16, 17, 18, 19, 20, 21, 22, 23],
        fps=10.0,
        loop=True,
        fallback="idle",
        loop_start=0,
    ),
    "waving": Animation(
        # Row 3: frames 24-31 (only 4 used)
        frames=[24, 25, 26, 27],
        fps=8.0,
        loop=True,
        fallback="idle",
        loop_start=0,
    ),
    "jumping": Animation(
        # Row 4: frames 32-39 (only 5 used)
        frames=[32, 33, 34, 35, 36],
        fps=8.0,
        loop=True,
        fallback="idle",
        loop_start=0,
    ),
    "failed": Animation(
        # Row 5: frames 40-47
        frames=[40, 41, 42, 43, 44, 45, 46, 47],
        fps=8.0,
        loop=True,
        fallback="idle",
        loop_start=0,
    ),
    "waiting": Animation(
        # Row 6: frames 48-55 (only 6 used)
        frames=[48, 49, 50, 51, 52, 53],
        fps=8.0,
        loop=True,
        fallback="idle",
        loop_start=0,
    ),
    "review": Animation(
        # Row 8: frames 64-71 (only 6 used)
        frames=[64, 65, 66, 67, 68, 69],
        fps=8.0,
        loop=True,
        fallback="idle",
        loop_start=0,
    ),
}
