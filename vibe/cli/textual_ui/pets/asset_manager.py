"""Asset manager for downloading and caching built-in pet spritesheets."""
from __future__ import annotations

from pathlib import Path
import shutil
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from vibe.cli.textual_ui.pets.constants import (
    BUILTIN_PETS,
    PET_CDN_BASE_URL,
    PET_PACK_VERSION,
    SPRITESHEET_HEIGHT,
    SPRITESHEET_WIDTH,
)


class AssetManager:
    """Manages downloading and caching of built-in pet assets.

    Downloads spritesheets from Codex CDN:
    https://persistent.oaistatic.com/codex/pets/v1/{pet_id}.webp

    Caches to: ~/.vibe/cache/pets/v1/assets/{pet_id}.webp
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Initialize asset manager.

        Args:
            cache_dir: Base cache directory. If None, uses ~/.vibe/cache
        """
        if cache_dir is None:
            from vibe.core.paths import VIBE_HOME

            self._base_cache_dir = VIBE_HOME.path / "cache"
        else:
            self._base_cache_dir = cache_dir

        # Versioned cache directory: cache/pets/v1/
        self.cache_dir = self._base_cache_dir / "pets" / PET_PACK_VERSION
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Assets subdirectory: cache/pets/v1/assets/
        self.assets_dir = self.cache_dir / "assets"
        self.assets_dir.mkdir(parents=True, exist_ok=True)

    def ensure_builtin_pet(self, pet_id: str) -> Path | None:
        """Ensure a built-in pet's spritesheet is available locally.

        Downloads from CDN if not cached, or returns cached path.

        Args:
            pet_id: The built-in pet ID (e.g., "codex")

        Returns:
            Path to the spritesheet file, or None if failed
        """
        if not self._is_valid_pet_id(pet_id):
            return None

        cached_path = self._get_cached_path(pet_id)

        # Check if already cached and valid
        if cached_path.exists() and self.validate_cached_spritesheet(cached_path):
            return cached_path

        # Download from CDN
        return self.download_spritesheet(pet_id)

    def download_spritesheet(self, pet_id: str) -> Path | None:
        """Download a spritesheet from the Codex CDN.

        Args:
            pet_id: The built-in pet ID

        Returns:
            Path to the downloaded file, or None if download failed
        """
        url = f"{PET_CDN_BASE_URL}/{pet_id}.webp"
        output_path = self._get_cached_path(pet_id)

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result = None
        try:
            # Download with timeout (60 seconds)
            with urlopen(url, timeout=60) as response:
                # Check Content-Length header for size limit
                content_length = response.getheader('Content-Length')
                if content_length:
                    size_bytes = int(content_length)
                    max_size = 4 * 1024 * 1024  # 4 MB
                    if size_bytes > max_size:
                        import logging

                        logger = logging.getLogger(__name__)
                        logger.warning(
                            f"Pet {pet_id} spritesheet too large: "
                            f"{size_bytes / (1024*1024):.1f}MB > {max_size / (1024*1024)}MB"
                        )
                        return None

                # Write to temporary file first (atomic operation)
                temp_path = output_path.with_suffix('.tmp')

                with open(temp_path, 'wb') as f:
                    shutil.copyfileobj(response, f)

                # Validate before moving to final location
                if self.validate_cached_spritesheet(temp_path):
                    # Atomic rename
                    temp_path.rename(output_path)
                    result = output_path
        except HTTPError as e:
            # Server returned error status
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"HTTP error downloading pet {pet_id}: {e.code} {e.reason}")
        except URLError as e:
            # Network error (DNS, connection, timeout)
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"URL error downloading pet {pet_id}: {e.reason}")
        except TimeoutError:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Timeout downloading pet {pet_id}")
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Unexpected error downloading pet {pet_id}: {e}")
        return result

    def validate_cached_spritesheet(self, path: Path) -> bool:
        """Validate that a cached spritesheet has correct dimensions.

        Args:
            path: Path to the spritesheet file

        Returns:
            True if valid, False otherwise
        """
        try:
            from PIL import Image  # type: ignore[import-untyped]

            with Image.open(path) as img:
                return img.size == (SPRITESHEET_WIDTH, SPRITESHEET_HEIGHT)
        except ImportError:
            # PIL not installed, skip validation
            return True
        except Exception:
            return False

    def clear_cache(self) -> None:
        """Clear all cached assets."""
        if self.assets_dir.exists():
            shutil.rmtree(self.assets_dir)
            self.assets_dir.mkdir()

    def get_cache_info(self) -> dict:
        """Get information about cached assets (for debugging)."""
        cached = []
        for pet_id in BUILTIN_PETS:
            path = self._get_cached_path(pet_id)
            if path.exists():
                stat = path.stat()
                cached.append({
                    "pet_id": pet_id,
                    "path": str(path),
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                })

        return {
            "cache_dir": str(self.cache_dir),
            "assets_dir": str(self.assets_dir),
            "cached_pets": cached,
            "total_cached": len(cached),
            "total_builtin": len(BUILTIN_PETS),
        }

    def _get_cached_path(self, pet_id: str) -> Path:
        """Get the cache path for a pet's spritesheet."""
        return self.assets_dir / f"{pet_id}.webp"

    def _is_valid_pet_id(self, pet_id: str) -> bool:
        """Check if a pet_id is a valid built-in pet."""
        return pet_id in BUILTIN_PETS


# --- Standalone Functions ---


def get_asset_manager(cache_dir: Path | None = None) -> AssetManager:
    """Convenience function to create an AssetManager.

    Args:
        cache_dir: Optional base cache directory

    Returns:
        AssetManager instance
    """
    return AssetManager(cache_dir)
