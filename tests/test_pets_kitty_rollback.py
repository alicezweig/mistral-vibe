#!/usr/bin/env python3
"""Test Kitty terminal detection after rollback."""

from __future__ import annotations

import os
from pathlib import Path
import sys

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vibe.cli.textual_ui.pets.image_protocol import (
    ImageProtocol,
    PetImageSupport,
    detect_kitty_terminal,
)


def test_kitty_terminal_detection_with_term():
    """Test detection via TERM environment variable."""
    # Test Kitty
    os.environ["TERM"] = "xterm-kitty"
    os.environ.pop("TERM_PROGRAM", None)
    assert detect_kitty_terminal() == True, "Kitty via TERM not detected"

    # Test Ghostty
    os.environ["TERM"] = "ghostty"
    assert detect_kitty_terminal() == True, "Ghostty via TERM not detected"

    # Test WezTerm
    os.environ["TERM"] = "wezterm"
    assert detect_kitty_terminal() == True, "WezTerm via TERM not detected"

    # Cleanup
    os.environ.pop("TERM", None)
    print("✓ TERM-based detection works")


def test_kitty_terminal_detection_with_term_program():
    """Test detection via TERM_PROGRAM environment variable."""
    os.environ.pop("TERM", None)

    # Test Kitty
    os.environ["TERM_PROGRAM"] = "kitty"
    assert detect_kitty_terminal() == True, "Kitty via TERM_PROGRAM not detected"

    # Test WezTerm
    os.environ["TERM_PROGRAM"] = "WezTerm"
    assert detect_kitty_terminal() == True, "WezTerm via TERM_PROGRAM not detected"

    # Cleanup
    os.environ.pop("TERM_PROGRAM", None)
    print("✓ TERM_PROGRAM-based detection works")


def test_iterm2_detection():
    """Test iTerm2 detection with version check."""
    os.environ.pop("TERM", None)

    # Old iTerm2 (< 3.6.0) - should NOT detect
    os.environ["TERM_PROGRAM"] = "iTerm.app"
    os.environ["TERM_PROGRAM_VERSION"] = "3.5.0"
    assert detect_kitty_terminal() == False, "Old iTerm2 should NOT be detected"

    # Recent iTerm2 (≥ 3.6.0) - should detect
    os.environ["TERM_PROGRAM_VERSION"] = "3.6.0"
    assert detect_kitty_terminal() == True, "Recent iTerm2 should be detected"

    # Newest iTerm2
    os.environ["TERM_PROGRAM_VERSION"] = "3.7.0"
    assert detect_kitty_terminal() == True, "Newest iTerm2 should be detected"

    # Cleanup
    os.environ.pop("TERM_PROGRAM", None)
    os.environ.pop("TERM_PROGRAM_VERSION", None)
    print("✓ iTerm2 version detection works")


def test_pet_image_support_detection():
    """Test full PetImageSupport detection flow."""
    os.environ.pop("TMUX", None)
    os.environ.pop("ZIJELLI", None)
    os.environ.pop("STY", None)

    # Test Kitty terminal
    os.environ["TERM"] = "xterm-kitty"
    os.environ.pop("TERM_PROGRAM", None)
    support = PetImageSupport.detect()
    assert support.is_supported == True, f"Kitty not supported: {support.reason}"
    assert support.protocol == ImageProtocol.KITTY, (
        f"Wrong protocol: {support.protocol}"
    )

    # Cleanup
    os.environ.pop("TERM", None)
    print("✓ PetImageSupport detection works")


if __name__ == "__main__":
    test_kitty_terminal_detection_with_term()
    test_kitty_terminal_detection_with_term_program()
    test_iterm2_detection()
    test_pet_image_support_detection()
    print("\nAll automated tests passed!")
