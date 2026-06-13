"""Pets module public API.

This module provides the main interface for loading, managing, and displaying
animated pets in Mistral Vibe. Pets respond to application state changes with
different animations (idle, running, waiting, review, failed).

Supported terminals:
- Kitty protocol terminals (Kitty, Ghostty, WezTerm, iTerm2 >= 3.6.0)
- Windows Terminal (Sixel protocol)

Usage:
    from vibe.cli.textual_ui.pets import load_pet, PetWidget, PetNotificationKind

    # Load a pet
    ambient_pet = load_pet("codex", cache_dir)

    # Update pet state
    ambient_pet.set_notification(PetNotificationKind.RUNNING, None)
"""
from __future__ import annotations

from vibe.cli.textual_ui.pets.asset_manager import AssetManager
from vibe.cli.textual_ui.pets.catalog import (
    get_all_available_pets,
    get_builtin_pet,
    is_builtin_pet,
)
from vibe.cli.textual_ui.pets.constants import (
    # Pet IDs
    BUILTIN_PETS,
    CUSTOM_PET_PREFIX,
    # Default animations
    DEFAULT_ANIMATIONS,
    DEFAULT_FRAME_COLUMNS,
    DEFAULT_FRAME_HEIGHT,
    DEFAULT_FRAME_ROWS,
    # Frame dimensions
    DEFAULT_FRAME_WIDTH,
    DEFAULT_PET_ID,
    DISABLED_PET_ID,
    KITTY_IMAGE_ID,
    MAX_ANIMATION_FPS,
    # Maximum limits
    MAX_PET_FRAMES,
    # Pet pack configuration
    PET_CDN_BASE_URL,
    PET_COMPOSER_GAP_PX,
    # Image protocol
    PET_IMAGE_ID,
    PET_PACK_DIR,
    PET_PACK_VERSION,
    PET_TARGET_HEIGHT_PX,
    SPRITESHEET_HEIGHT,
    SPRITESHEET_WIDTH,
    # Display layout
    TERMINAL_ROW_HEIGHT_PX,
)
from vibe.cli.textual_ui.pets.frame_extractor import FrameExtractor
from vibe.cli.textual_ui.pets.image_protocol import (
    ImageProtocol,
    KittyEncoder,
    PetImageSupport,
    SixelEncoder,
    detect_iterm2_kitty_support,
    detect_kitty_terminal,
    detect_multiplexer,
    detect_sixel_support,
    detect_windows_terminal,
)
from vibe.cli.textual_ui.pets.models import (
    AmbientPet,
    Animation,
    Pet,
    PetNotification,
    PetNotificationKind,
)
from vibe.cli.textual_ui.widgets.pet_widget import PetWidget

# --- Public Functions ---

def load_pet(pet_id: str, cache_dir: Path | None = None) -> AmbientPet | None:
    """Load a pet by ID, downloading assets if needed and extracting frames.

    This is the main entry point for loading pets. It handles:
    - Checking terminal support
    - Loading built-in or custom pets
    - Downloading spritesheets from CDN (for built-in pets)
    - Extracting individual frames from spritesheets
    - Validating all assets

    Args:
        pet_id: The pet ID to load (e.g., "codex", "dewey", or custom pet ID)
        cache_dir: Base cache directory. If None, uses ~/.vibe/cache

    Returns:
        AmbientPet object ready for display, or None if loading failed

    Raises:
        PetLoadError: If pet cannot be loaded (invalid ID, missing files)
        PetUnsupportedError: If terminal does not support image protocols
    """
    from pathlib import Path

    if pet_id is None:
        return None

    # Special case: disabled pets
    if pet_id == DISABLED_PET_ID:
        return None

    # Import here to avoid circular imports
    from vibe.core.paths import CACHE_DIR

    # Determine cache directory
    if cache_dir is None:
        base_cache_dir = CACHE_DIR
    else:
        base_cache_dir = Path(cache_dir)

    # Check terminal support first (fail fast if not supported)
    support = PetImageSupport.detect()
    if not support.is_supported:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Pets not supported: {support.reason}")
        return None

    # Try to load pet definition
    pet: Pet | None = None

    if pet_id in BUILTIN_PETS:
        # Built-in pet
        pet = get_builtin_pet(pet_id, base_cache_dir)
    else:
        # Custom pet - try to load from ~/.vibe/pets/<pet-id>/pet.json
        custom_dir = base_cache_dir.parent / "pets" / pet_id
        manifest_path = custom_dir / "pet.json"
        if manifest_path.exists():
            try:
                pet = Pet.from_manifest(manifest_path)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to load custom pet {pet_id}: {e}")
                return None
        else:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Custom pet {pet_id} not found at {custom_dir}")
            return None

    if pet is None:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Pet {pet_id} not found (not built-in or custom)")
        return None

    # Validate pet configuration
    try:
        pet.validate()
    except AssertionError as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Invalid pet configuration for {pet_id}: {e}")
        return None

    # Get spritesheet path
    if pet_id in BUILTIN_PETS:
        # For built-in pets, use the cached spritesheet from asset manager
        asset_mgr = AssetManager(base_cache_dir)
        spritesheet_path = asset_mgr.ensure_builtin_pet(pet_id)
    else:
        # For custom pets, spritesheet should be in the same directory as manifest
        spritesheet_path = custom_dir / pet.spritesheet_path.name

    if spritesheet_path is None or not spritesheet_path.exists():
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Spritesheet not found for pet {pet_id}")
        return None

    # Extract frames
    cache_key = FrameExtractor.cache_key(pet)
    frame_cache_dir = base_cache_dir / "pets" / PET_PACK_VERSION / "frame-cache" / pet.id / cache_key / "frames"

    try:
        frames = FrameExtractor.extract_frames(pet, spritesheet_path, frame_cache_dir)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to extract frames for pet {pet_id}: {e}")
        return None

    if len(frames) == 0:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"No frames extracted for pet {pet_id}")
        return None

    # Create and return AmbientPet
    return AmbientPet(
        pet=pet,
        frames=frames,
        support=support.protocol,
        animations_enabled=True,
        notification=None,
        animation_started_at=__import__('time').time(),
    )


def get_pet_draw_request(
    ambient_pet: AmbientPet,
    area_width: int,
    area_height: int,
    composer_bottom_y: int,
    anchor: str = "composer",
) -> tuple[bool, int, int, int, int] | None:
    """Calculate draw request parameters for a pet frame.

    This determines where and how to render the pet based on:
    - Current frame
    - Available area
    - Anchor position
    - Terminal row height

    Args:
        ambient_pet: The AmbientPet to render
        area_width: Width of available area in pixels
        area_height: Height of available area in pixels
        composer_bottom_y: Y position of composer bottom in pixels
        anchor: Anchor position ("composer" or "screen_bottom")

    Returns:
        Tuple of (should_render, x, y, width_px, height_px) or None
    """
    if not ambient_pet.frames:
        return None

    # Calculate target image size
    aspect_ratio = ambient_pet.pet.frame_width / ambient_pet.pet.frame_height
    height_px = PET_TARGET_HEIGHT_PX
    width_px = int(height_px * aspect_ratio)

    # Calculate position based on anchor
    if anchor == "screen_bottom":
        y = area_height - height_px - PET_COMPOSER_GAP_PX
    else:  # "composer"
        y = composer_bottom_y - height_px - PET_COMPOSER_GAP_PX

    # Right-align with gap from right edge
    x = area_width - width_px - 10

    # Check if pet fits in area
    if x < 0 or y < 0 or width_px > area_width or height_px > area_height:
        return None

    return (True, x, y, width_px, height_px)


# --- Exports ---

__all__ = [
    # Models
    "Pet",
    "Animation", 
    "AmbientPet",
    "PetNotification",
    "PetNotificationKind",
    # Widget
    "PetWidget",
    # Catalog
    "BUILTIN_PETS",
    "DEFAULT_PET_ID",
    "DISABLED_PET_ID",
    "CUSTOM_PET_PREFIX",
    "DEFAULT_ANIMATIONS",
    "DEFAULT_FRAME_WIDTH",
    "DEFAULT_FRAME_HEIGHT",
    "DEFAULT_FRAME_COLUMNS",
    "DEFAULT_FRAME_ROWS",
    "SPRITESHEET_WIDTH",
    "SPRITESHEET_HEIGHT",
    "PET_CDN_BASE_URL",
    "PET_PACK_VERSION",
    "PET_PACK_DIR",
    "MAX_PET_FRAMES",
    "MAX_ANIMATION_FPS",
    "get_builtin_pet",
    "get_all_available_pets",
    "is_builtin_pet",
    # Image protocol
    "ImageProtocol",
    "PetImageSupport",
    "KittyEncoder",
    "SixelEncoder",
    "detect_multiplexer",
    "detect_kitty_terminal",
    "detect_iterm2_kitty_support",
    "detect_sixel_support",
    "detect_windows_terminal",
    "PET_IMAGE_ID",
    "KITTY_IMAGE_ID",
    "PET_TARGET_HEIGHT_PX",
    # Asset management
    "AssetManager",
    # Frame extraction
    "FrameExtractor",
    # Public functions
    "load_pet",
    "get_pet_draw_request",
    # Display layout constants
    "TERMINAL_ROW_HEIGHT_PX",
    "PET_COMPOSER_GAP_PX",
]
