from __future__ import annotations

"""Terminal image protocol detection and encoding for pets.
Supports: Kitty protocol terminals and Windows Terminal (Sixel protocol).
"""
import base64
from dataclasses import dataclass
from enum import StrEnum, auto
import io
import os
from pathlib import Path

from PIL import Image

from vibe.cli.textual_ui.pets.constants import KITTY_IMAGE_ID

# --- Enums ---


class ImageProtocol(StrEnum):
    """Supported terminal image protocols."""

    KITTY = auto()  # Kitty graphics protocol
    SIXEL = auto()  # Sixel protocol (Windows Terminal)
    UNSUPPORTED = auto()


# --- Support Detection ---


@dataclass
class PetImageSupport:
    """Result of terminal image protocol detection."""

    protocol: ImageProtocol
    is_supported: bool
    reason: str | None  # If unsupported, the reason

    @classmethod
    def detect(cls) -> PetImageSupport:
        """Detect which image protocol the current terminal supports.

        Returns:
            PetImageSupport with protocol, support status, and reason
        """
        # Check for multiplexer first (blocks all protocols)
        if detect_multiplexer():
            return cls(
                ImageProtocol.UNSUPPORTED,
                False,
                "Terminal multiplexer detected (tmux/zellij/screen)",
            )

        # Try Kitty protocol
        if detect_kitty_terminal():
            return cls(ImageProtocol.KITTY, True, None)

        # Try Sixel protocol (Windows Terminal)
        if detect_sixel_support():
            return cls(ImageProtocol.SIXEL, True, None)

        return cls(ImageProtocol.UNSUPPORTED, False, "No supported image protocol")


# --- Detection Functions ---


def detect_multiplexer() -> bool:
    """Detect if running inside a terminal multiplexer.
    Multiplexers intercept escape sequences and break image protocols.

    Returns:
        True if running in tmux, zellij, or screen
    """
    return bool(
        os.environ.get("TMUX")  # tmux
        or os.environ.get("ZIJELLI")  # Zellij
        or os.environ.get("STY")  # GNU screen
    )


def detect_kitty_terminal() -> bool:
    """Detect if terminal supports Kitty graphics protocol.
    
    Supports: Kitty terminal, Ghostty, WezTerm, iTerm2 >= 3.6.0

    Returns:
        True if terminal supports Kitty protocol
    """
    term = os.environ.get("TERM", "").lower()
    term_program = os.environ.get("TERM_PROGRAM", "").lower()
    
    # Check TERM for known Kitty-supporting terminals
    if any(t in term for t in ["kitty", "ghostty", "wezterm"]):
        return True
    
    # Check TERM_PROGRAM for known Kitty-supporting terminals
    if any(t in term_program for t in ["kitty", "ghostty", "wezterm"]):
        return True
    
    # Special case: iTerm2 requires version check
    if "iterm" in term or "iterm" in term_program:
        return detect_iterm2_kitty_support()
    
    return False


def detect_iterm2_kitty_support() -> bool:
    """Check if iTerm2 version supports Kitty protocol (>= 3.6.0)."""
    version_str = os.environ.get("ITERM2_VERSION", "")
    # Also check TERM_PROGRAM_VERSION
    if not version_str:
        version_str = os.environ.get("TERM_PROGRAM_VERSION", "")
    
    try:
        parts = version_str.split(".")
        major = int(parts[0]) if len(parts) > 0 else 3
        minor = int(parts[1]) if len(parts) > 1 else 6
        patch = int(parts[2]) if len(parts) > 2 else 0
        return (major, minor, patch) >= (3, 6, 0)
    except (ValueError, IndexError):
        # Cannot parse, assume recent
        return True


def detect_sixel_support() -> bool:
    """Detect if terminal supports Sixel graphics protocol.
    Currently only checks for Windows Terminal.

    Returns:
        True if Windows Terminal is detected
    """
    return detect_windows_terminal()


def detect_windows_terminal() -> bool:
    """Detect if running in Windows Terminal.

    Windows Terminal has built-in Sixel support since version 1.15 (2023).
    No configuration needed from the user.

    Returns:
        True if WT_SESSION or TERM_PROGRAM indicates Windows Terminal
    """
    # Method 1: WT_SESSION environment variable (most reliable)
    if os.environ.get("WT_SESSION"):
        return True

    # Method 2: TERM_PROGRAM environment variable
    term_program = os.environ.get("TERM_PROGRAM", "").lower()
    if "windows terminal" in term_program or term_program == "wt":
        return True

    return False


# --- Kitty Protocol Encoder ---


class KittyEncoder:
    """Encoder for Kitty graphics protocol.

    Kitty protocol uses escape sequences to transmit images:
    - Transmit: \\x1b_Ga=d;w=W;h=H;<base64_data>\\x1b\\\
    - Delete: \\x1b_Gi=ID\\x1b\\\

    Reference: https://sw.kovidgoyal.net/kitty/graphics-protocol/
    """

    # Fixed image ID for pets
    IMAGE_ID = KITTY_IMAGE_ID

    @staticmethod
    def transmit_png(png_path: Path, image_id: int = IMAGE_ID) -> str:
        """Generate Kitty protocol escape sequence for a PNG image.

        Args:
            png_path: Path to PNG file
            image_id: Kitty image ID (0-255, default: 0xC0DE)

        Returns:
            Escape sequence string to transmit the image
        """
        with Image.open(png_path) as img:
            # Convert to RGBA if needed (Kitty works best with RGBA)
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            width, height = img.size

            # Encode PNG as base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            b64_data = base64.b64encode(buffered.getvalue()).decode("ascii")

            # Build Kitty command
            # a=d means "display image data"
            # w=width, h=height are image dimensions
            # Base64 data follows, then ST (\x1b\\\
            return f"\x1b_Ga=d;w={width};h={height};{b64_data}\x1b\\"

    @staticmethod
    def transmit_png_bytes(
        png_bytes: bytes, width: int, height: int, image_id: int = IMAGE_ID
    ) -> str:
        """Generate Kitty sequence from raw PNG bytes.

        Args:
            png_bytes: Raw PNG data
            width: Image width in pixels
            height: Image height in pixels
            image_id: Kitty image ID

        Returns:
            Escape sequence string
        """
        b64_data = base64.b64encode(png_bytes).decode("ascii")
        return f"\x1b_Ga=d;w={width};h={height};{b64_data}\x1b\\"

    @staticmethod
    def delete_image(image_id: int = IMAGE_ID) -> str:
        """Generate Kitty command to delete a previously transmitted image.

        Args:
            image_id: Kitty image ID to delete

        Returns:
            Escape sequence string
        """
        return f"\x1b_Gi={image_id}\x1b\\"

    @staticmethod
    def delete_all_images() -> str:
        """Generate Kitty command to delete all images (IDs 0-4).

        Returns:
            Escape sequence string
        """
        return "\x1b_Gi=0;1;2;3;4\x1b\\"


# --- Sixel Protocol Encoder ---


class SixelEncoder:
    """Encoder for Sixel graphics protocol.

    Sixel uses Device Control String (DCS) to transmit images:
    - Start: \\x1bPq
    - Sixel data
    - End: \\x1b\\\

    Reference: https://en.wikipedia.org/wiki/Sixel
    """

    @staticmethod
    def encode_sixel(png_path: Path, height_px: int) -> bytes:
        """Convert PNG to Sixel format, resized to target height.

        Tries multiple methods in order:
        1. PIL's built-in Sixel support (if compiled with libsixel)
        2. External 'sixel' package
        3. Returns empty bytes (will fail gracefully)

        Args:
            png_path: Path to PNG file
            height_px: Target height in pixels (maintains aspect ratio)

        Returns:
            Sixel-encoded bytes, or empty bytes if encoding fails
        """
        # Method 1: Try PIL's built-in Sixel support
        try:
            with Image.open(png_path) as img:
                # Calculate new width maintaining aspect ratio
                aspect_ratio = img.width / img.height
                new_width = int(height_px * aspect_ratio)

                # Resize using Lanczos (high quality)
                img = img.resize((new_width, height_px), Image.Resampling.LANCZOS)

                # Convert to RGB (Sixel typically works with RGB)
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Encode to Sixel
                # Note: tobytes() with "SIXEL" format may not be available
                # if PIL wasn't compiled with libsixel support
                return img.tobytes("SIXEL", "P")
        except (ValueError, AttributeError, TypeError, OSError):
            # PIL doesn't have Sixel support compiled in
            pass

        # Method 2: Try external 'sixel' package
        try:
            import sixel  # pyright: ignore[reportMissingImports]

            with Image.open(png_path) as img:
                aspect_ratio = img.width / img.height
                new_width = int(height_px * aspect_ratio)
                img = img.resize((new_width, height_px), Image.Resampling.LANCZOS)

                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Use sixel package encoder
                encoder = sixel.Encoder()
                return encoder.encode(img)
        except ImportError:
            # sixel package not installed
            pass

        # Method 3: Fallback - return empty bytes
        # Caller will handle this gracefully
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(
            "Sixel encoding failed. Install 'sixel' package for better support: "
            "pip install sixel"
        )
        return b""

    @staticmethod
    def transmit(sixel_data: bytes) -> str:
        """Wrap Sixel data in DCS (Device Control String) sequences.

        Args:
            sixel_data: Raw Sixel-encoded bytes

        Returns:
            Complete escape sequence string ready for transmission
        """
        # DCS prefix + Sixel data + ST (String Terminator)
        # Sixel data should be decoded as latin-1 (ISO-8859-1)
        try:
            sixel_str = sixel_data.decode("latin-1")
        except UnicodeDecodeError:
            # Fallback to UTF-8 with replacement
            sixel_str = sixel_data.decode("utf-8", errors="replace")

        return f"\x1bPq{sixel_str}\x1b\\"


# --- Public API ---

__all__ = [
    "ImageProtocol",
    "KittyEncoder",
    "PetImageSupport",
    "SixelEncoder",
    "detect_iterm2_kitty_support",
    "detect_kitty_terminal",
    "detect_multiplexer",
    "detect_sixel_support",
    "detect_windows_terminal",
]
