"""Pet catalog with built-in pet definitions and default animations."""

from __future__ import annotations

from pathlib import Path

from vibe.cli.textual_ui.pets.constants import (
    BUILTIN_PETS,
    DEFAULT_ANIMATIONS,
    DEFAULT_FRAME_COLUMNS,
    DEFAULT_FRAME_HEIGHT,
    DEFAULT_FRAME_ROWS,
    DEFAULT_FRAME_WIDTH,
)
from vibe.cli.textual_ui.pets.models import Pet

# --- Functions ---


def get_builtin_pet(pet_id: str, cache_dir: Path) -> Pet | None:
    """Create and return a Pet object for a built-in pet.

    Args:
        pet_id: The ID of the built-in pet (e.g., "codex")
        cache_dir: Base cache directory (e.g., ~/.vibe/cache)

    Returns:
        Pet object or None if pet_id is not a built-in pet
    """
    from vibe.cli.textual_ui.pets.asset_manager import AssetManager

    if pet_id not in BUILTIN_PETS:
        return None

    asset_mgr = AssetManager(cache_dir)
    spritesheet_path = asset_mgr.ensure_builtin_pet(pet_id)

    if spritesheet_path is None:
        return None

    # Create display name (title case, replace hyphens with spaces)
    display_name = pet_id.title().replace("-", " ")

    return Pet(
        id=pet_id,
        display_name=display_name,
        description=f"Built-in {pet_id} pet from Codex",
        spritesheet_path=spritesheet_path,
        frame_width=DEFAULT_FRAME_WIDTH,
        frame_height=DEFAULT_FRAME_HEIGHT,
        columns=DEFAULT_FRAME_COLUMNS,
        rows=DEFAULT_FRAME_ROWS,
        animations=DEFAULT_ANIMATIONS.copy(),
    )


def get_all_available_pets(cache_dir: Path) -> list[Pet]:
    """Get all available pets (built-in + custom).

    Args:
        cache_dir: Base cache directory

    Returns:
        List of Pet objects, sorted alphabetically
    """
    pets = []

    # Add built-in pets
    for pet_id in BUILTIN_PETS:
        pet = get_builtin_pet(pet_id, cache_dir)
        if pet:
            pets.append(pet)

    # Add custom pets from ~/.vibe/pets/
    custom_base = cache_dir.parent / "pets"
    if custom_base.exists():
        for pet_dir in sorted(custom_base.iterdir()):
            if pet_dir.is_dir():
                manifest_path = pet_dir / "pet.json"
                if manifest_path.exists():
                    try:
                        pet = Pet.from_manifest(manifest_path)
                        pets.append(pet)
                    except Exception as e:
                        import logging

                        logger = logging.getLogger(__name__)
                        logger.warning(f"Failed to load custom pet {pet_dir.name}: {e}")

    # Sort by display name
    pets.sort(key=lambda p: p.display_name.lower())

    return pets


def is_builtin_pet(pet_id: str) -> bool:
    """Check if a pet ID is a built-in pet."""
    return pet_id in BUILTIN_PETS
