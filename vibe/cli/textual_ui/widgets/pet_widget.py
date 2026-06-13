"""Textual widget for displaying animated pets.

This widget renders pet frames using either Kitty graphics protocol
(Kitty, Ghostty, WezTerm, iTerm2) or Sixel protocol (Windows Terminal),
depending on terminal support.
"""
from __future__ import annotations

from pathlib import Path
import sys
from typing import ClassVar

from textual.widget import Widget

from vibe.cli.textual_ui.pets.constants import PET_TARGET_HEIGHT_PX
from vibe.cli.textual_ui.pets.image_protocol import (
    ImageProtocol,
    KittyEncoder,
    SixelEncoder,
)
from vibe.cli.textual_ui.pets.models import AmbientPet, PetNotificationKind


class PetWidget(Widget):
    """Textual widget that displays the animated pet.

    The pet animation automatically updates based on the ambient pet's state.
    Uses Kitty protocol for Kitty-compatible terminals and Sixel protocol for Windows Terminal.

    Attributes:
        ambient_pet: The AmbientPet being displayed, or None if no pet
    """

    DEFAULT_CLASSES: ClassVar[str] = "pet-widget"

    def __init__(self, ambient_pet: AmbientPet | None = None) -> None:
        """Initialize the pet widget.

        Args:
            ambient_pet: Optional AmbientPet to display initially
        """
        super().__init__()
        self.ambient_pet = ambient_pet
        self._last_frame_index: int = -1
        self._last_protocol: ImageProtocol | None = None
        self._visible: bool = True

    def on_mount(self) -> None:
        """Called when widget is mounted into the DOM."""
        # Start animation timer at ~24 FPS
        # This checks if the frame needs updating and re-renders if so
        self.set_interval(1 / 24, self._update_frame)

    def on_unmount(self) -> None:
        """Called when widget is unmounted from the DOM."""
        # Clean up any displayed image
        self._clear_image()

    def _update_frame(self) -> None:
        """Check if frame needs updating and render if so."""
        if not self._visible or not self.ambient_pet:
            return

        current_index = self.ambient_pet.current_frame_index()

        if current_index != self._last_frame_index:
            self._last_frame_index = current_index
            self._render_frame()

    def _render_frame(self) -> None:
        """Render the current frame to the terminal."""
        if not self.ambient_pet:
            return

        frame_index = self.ambient_pet.current_frame_index()

        # Safety check: ensure frame index is valid
        if frame_index < 0 or frame_index >= len(self.ambient_pet.frames):
            return

        frame_path = self.ambient_pet.frames[frame_index]

        # Encode and transmit based on protocol
        if self.ambient_pet.support == ImageProtocol.KITTY:
            self._render_kitty(frame_path)
        elif self.ambient_pet.support == ImageProtocol.SIXEL:
            self._render_sixel(frame_path)

    def _render_kitty(self, frame_path: Path) -> None:
        """Render frame using Kitty graphics protocol."""
        # Generate and send Kitty escape sequence
        sequence = KittyEncoder.transmit_png(frame_path)

        # Write directly to stdout
        # Note: This bypasses Textual's rendering for direct terminal control
        sys.stdout.write(sequence)
        sys.stdout.flush()

    def _render_sixel(self, frame_path: Path) -> None:
        """Render frame using Sixel protocol."""
        # Encode to Sixel at target height
        sixel_data = SixelEncoder.encode_sixel(frame_path, PET_TARGET_HEIGHT_PX)

        if not sixel_data:
            # Encoding failed, try without resizing
            sixel_data = SixelEncoder.encode_sixel(frame_path, 0)

        if sixel_data:
            sequence = SixelEncoder.transmit(sixel_data)
            sys.stdout.write(sequence)
            sys.stdout.flush()

    def _clear_image(self) -> None:
        """Clear the currently displayed image."""
        if not self.ambient_pet:
            return

        if self.ambient_pet.support == ImageProtocol.KITTY:
            sequence = KittyEncoder.delete_image()
            sys.stdout.write(sequence)
            sys.stdout.flush()
        # Sixel: No standard delete command, will be overwritten on next render

    def set_pet(self, ambient_pet: AmbientPet | None) -> None:
        """Set the pet to display.

        Args:
            ambient_pet: The AmbientPet to display, or None to clear
        """
        # Clear old image
        if self.ambient_pet:
            self._clear_image()

        self.ambient_pet = ambient_pet
        self._last_frame_index = -1
        self._visible = ambient_pet is not None

        if ambient_pet:
            self._render_frame()

    def set_notification(self, kind: PetNotificationKind, body: str | None) -> None:
        """Update the pet's notification state.

        This triggers an animation change based on the notification kind.

        Args:
            kind: The notification kind (RUNNING, WAITING, REVIEW, FAILED)
            body: Optional custom message for the notification
        """
        if self.ambient_pet:
            self.ambient_pet.set_notification(kind, body)
            self._update_frame()

    def clear_notification(self) -> None:
        """Clear the pet's notification, returning to idle animation."""
        if self.ambient_pet:
            self.ambient_pet.clear_notification()
            self._update_frame()

    def hide(self) -> None:
        """Hide the pet widget."""
        self._visible = False
        self._clear_image()

    def show(self) -> None:
        """Show the pet widget."""
        self._visible = True
        if self.ambient_pet:
            self._render_frame()

    @property
    def is_visible(self) -> bool:
        """Check if pet is currently visible."""
        return self._visible and self.ambient_pet is not None
