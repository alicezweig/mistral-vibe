"""Frame extractor for splitting spritesheets into individual frames."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    from vibe.cli.textual_ui.pets.models import Pet


class FrameExtractor:
    """Extracts individual frames from spritesheet images.

    Splits a spritesheet (e.g., 1536x1872px) into individual frames
    based on the grid dimensions (e.g., 8x9 grid of 192x208px frames).

    Results are cached to avoid re-extraction on subsequent runs.
    """

    @staticmethod
    def extract_frames(pet: Pet, spritesheet_path: Path, output_dir: Path) -> list[Path]:
        """Extract all frames from a spritesheet and save as individual PNGs.

        If all frames already exist and match the expected count,
        returns the existing frames without re-extraction.

        Args:
            pet: The Pet object with frame dimensions and grid info
            spritesheet_path: Path to the spritesheet image file
            output_dir: Directory to save extracted frames

        Returns:
            List of Path objects pointing to extracted frame files
        """
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Calculate expected number of frames
        expected_count = pet.get_total_frames()

        # Check if all frames already exist
        existing_frames = sorted(output_dir.glob("frame_*.png"))
        if len(existing_frames) == expected_count:
            # All frames exist, return them sorted by index
            return sorted(
                existing_frames,
                key=lambda p: int(p.stem.split("_")[1]),  # Extract number from "frame_NNN.png"
            )

        # Clear stale frames (if any exist)
        for stale_frame in existing_frames:
            stale_frame.unlink()

        # Extract all frames from spritesheet
        frames: list[Path] = []
        with Image.open(spritesheet_path) as spritesheet:
            for i in range(expected_count):
                # Extract single frame
                frame_img = FrameExtractor.extract_frame(
                    spritesheet,
                    i,
                    pet.frame_width,
                    pet.frame_height,
                    pet.columns,
                )

                # Save frame as PNG
                frame_path = output_dir / f"frame_{i:03d}.png"
                frame_img.save(frame_path, "PNG")
                frames.append(frame_path)

        return frames

    @staticmethod
    def extract_frame(
        spritesheet: Image.Image,
        frame_index: int,
        frame_width: int,
        frame_height: int,
        columns: int,
    ) -> Image.Image:
        """Extract a single frame from a spritesheet by its grid index.

        The spritesheet is treated as a grid with `columns` columns.
        Frame index 0 is at (0, 0), index 1 at (1, 0), etc.

        Args:
            spritesheet: The source spritesheet image
            frame_index: Index of the frame to extract (0-based)
            frame_width: Width of each frame in pixels
            frame_height: Height of each frame in pixels
            columns: Number of columns in the spritesheet grid

        Returns:
            A PIL Image object containing the extracted frame
        """
        # Calculate row and column from index
        row = frame_index // columns
        col = frame_index % columns

        # Calculate pixel coordinates
        left = col * frame_width
        upper = row * frame_height
        right = left + frame_width
        lower = upper + frame_height

        # Crop and return the frame
        return spritesheet.crop((left, upper, right, lower))

    @staticmethod
    def cache_key(pet: Pet) -> str:
        """Generate a cache key for a pet based on its dimensions.

        This ensures that if a pet's frame dimensions or grid layout
        changes, a new cache directory is used.

        Args:
            pet: The Pet object

        Returns:
            A string cache key
        """
        key = f"{pet.frame_width}x{pet.frame_height}-{pet.columns}x{pet.rows}"
        # Use SHA256 hash for consistent, short keys
        return f"sha256-{hashlib.sha256(key.encode()).hexdigest()[:16]}"

    @staticmethod
    def get_frame_cache_dir(pet: Pet, base_cache_dir: Path) -> Path:
        """Get the cache directory for a pet's extracted frames.

        Structure: base_cache_dir/frame-cache/<pet-id>/<cache-key>/frames/

        Args:
            pet: The Pet object
            base_cache_dir: Base cache directory (e.g., ~/.vibe/cache/pets)

        Returns:
            Path to the frame cache directory
        """
        cache_key = FrameExtractor.cache_key(pet)
        return base_cache_dir / "frame-cache" / pet.id / cache_key / "frames"


# --- Convenience Functions ---

def extract_all_frames(pet: Pet, spritesheet_path: Path, cache_dir: Path) -> list[Path]:
    """Convenience function to extract all frames for a pet.

    Uses the standard cache directory structure.

    Args:
        pet: The Pet object
        spritesheet_path: Path to the spritesheet
        cache_dir: Base cache directory

    Returns:
        List of Path objects to extracted frames
    """
    frame_cache_dir = FrameExtractor.get_frame_cache_dir(pet, cache_dir)
    return FrameExtractor.extract_frames(pet, spritesheet_path, frame_cache_dir)
