from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vibe.cli.textual_ui.pets.image_protocol import ImageProtocol


class PetNotificationKind(StrEnum):
    """Pet notification states mapped to animations."""

    RUNNING = "running"  # Task/turn in progress (LLM busy)
    WAITING = "waiting"  # Needs user input/approval
    REVIEW = "review"  # Ready for user review
    FAILED = "failed"  # Error occurred


@dataclass
class Animation:
    """Animation definition with frame sequence and timing."""

    frames: list[int]  # List of sprite indices into pet frames
    fps: float  # Frames per second
    loop: bool = True  # Whether animation loops
    fallback: str | None = None  # Animation to fall back to after one-shot
    loop_start: int | None = None  # Index where looping starts

    def validate(self, total_frames: int) -> None:
        """Validate animation configuration."""
        assert len(self.frames) > 0, "Animation must have at least one frame"

        # Check all frame indices are within bounds
        for frame_idx in self.frames:
            assert 0 <= frame_idx < total_frames, (
                f"Frame index {frame_idx} out of bounds (0-{total_frames - 1})"
            )

        # Check fallback exists if this is one-shot
        if not self.loop and self.fallback:
            # Will be validated when pet is fully loaded
            pass


@dataclass
class Pet:
    """Pet definition with spritesheet and animation data."""

    id: str
    display_name: str
    description: str
    spritesheet_path: Path  # Path to spritesheet (WebP or PNG)
    animations: dict[str, Animation]
    frame_width: int = 192  # Default from Codex
    frame_height: int = 208  # Default from Codex
    columns: int = 8  # Default from Codex
    rows: int = 9  # Default from Codex

    def get_total_frames(self) -> int:
        """Calculate total number of frames from grid."""
        return self.columns * self.rows

    def validate(self) -> None:
        """Validate pet configuration."""
        # Check dimensions are positive
        assert self.frame_width > 0, "frame_width must be positive"
        assert self.frame_height > 0, "frame_height must be positive"
        assert self.columns > 0, "columns must be positive"
        assert self.rows > 0, "rows must be positive"

        # Check frame count doesn't exceed maximum
        total = self.get_total_frames()
        assert total <= 256, f"Frame count {total} exceeds maximum of 256"

        # Validate animations
        for name, anim in self.animations.items():
            anim.validate(total)

    @classmethod
    def from_manifest(cls, manifest_path: Path) -> Pet:
        """Load pet from JSON manifest file."""
        import json

        with open(manifest_path) as f:
            data = json.load(f)

        # Map JSON keys to Python names (snake_case vs camelCase)
        animations = {}
        for name, anim_data in data.get("animations", {}).items():
            animations[name] = Animation(
                frames=anim_data["frames"],
                fps=anim_data.get("fps", 8.0),
                loop=anim_data.get("loop", True),
                fallback=anim_data.get("fallback"),
                loop_start=anim_data.get("loopStart") or anim_data.get("loop_start"),
            )

        # Handle both camelCase and snake_case for frame dimensions
        frame_data = data.get("frame", {})

        return cls(
            id=data.get(
                "id", data.get("displayName", "unknown").lower().replace(" ", "-")
            ),
            display_name=data.get(
                "displayName", data.get("display_name", "Unknown Pet")
            ),
            description=data.get("description", ""),
            spritesheet_path=Path(data["spritesheetPath"]),
            frame_width=frame_data.get("width", 192),
            frame_height=frame_data.get("height", 208),
            columns=frame_data.get("columns", 8),
            rows=frame_data.get("rows", 9),
            animations=animations,
        )


@dataclass
class PetNotification:
    """Notification state for pet, with expiration."""

    kind: PetNotificationKind
    body: str | None
    created_at: float = field(default_factory=time.time)

    # Notification lifetimes (in seconds) - match Codex
    RUNNING_LIFETIME = 180  # 3 minutes
    FAILED_LIFETIME = 3600  # 1 hour
    WAITING_LIFETIME = 86400  # 24 hours
    REVIEW_LIFETIME = 604800  # 7 days

    def is_expired(self) -> bool:
        """Check if notification has expired based on its lifetime."""
        elapsed = time.time() - self.created_at
        lifetime_attr = f"{self.kind.upper()}_LIFETIME"
        lifetime = getattr(self, lifetime_attr, self.REVIEW_LIFETIME)
        return elapsed >= lifetime

    @property
    def label(self) -> str:
        """Get human-readable label for this notification kind."""
        return {
            PetNotificationKind.RUNNING: "Running",
            PetNotificationKind.WAITING: "Needs input",
            PetNotificationKind.REVIEW: "Ready",
            PetNotificationKind.FAILED: "Blocked",
        }.get(self.kind, "Unknown")


@dataclass
class AmbientPet:
    """Manages pet state, animations, and rendering."""

    pet: Pet
    frames: list[Path]  # Paths to extracted PNG frames
    support: ImageProtocol  # Detected terminal protocol (from image_protocol module)
    animations_enabled: bool = True
    notification: PetNotification | None = None
    animation_started_at: float = field(default_factory=time.time)

    def current_animation(self) -> Animation:
        """Get current animation based on notification state."""
        if self.notification and not self.notification.is_expired():
            # Map notification kind to animation name
            mapping = {
                PetNotificationKind.RUNNING: "running",
                PetNotificationKind.WAITING: "waiting",
                PetNotificationKind.REVIEW: "review",
                PetNotificationKind.FAILED: "failed",
            }
            anim_name = mapping.get(self.notification.kind, "idle")
            if anim_name in self.pet.animations:
                return self.pet.animations[anim_name]

        # Default to idle
        return self.pet.animations["idle"]

    def current_frame_index(self) -> int:
        """Calculate current frame index based on animation timing."""
        anim = self.current_animation()
        elapsed = time.time() - self.animation_started_at
        frame_duration = 1.0 / anim.fps

        if anim.loop and anim.loop_start is not None:
            # Looping animation: cycle through frames from loop_start
            loop_frames = anim.frames[anim.loop_start :]
            loop_duration = len(loop_frames) * frame_duration
            elapsed = elapsed % loop_duration
            idx = int(elapsed / frame_duration) % len(loop_frames)
            return anim.frames[anim.loop_start + idx]
        else:
            # Non-looping or no loop_start
            idx = int(elapsed / frame_duration)
            if idx < len(anim.frames):
                return anim.frames[idx]
            # One-shot animation complete, use fallback
            if anim.fallback:
                fallback_anim = self.pet.animations.get(anim.fallback)
                if fallback_anim:
                    return fallback_anim.frames[0]

        return 0

    def set_notification(self, kind: PetNotificationKind, body: str | None) -> None:
        """Set notification state, resetting animation timer."""
        self.notification = PetNotification(kind, body)
        self.animation_started_at = time.time()

    def clear_notification(self) -> None:
        """Clear notification, returning to idle animation."""
        self.notification = None
        self.animation_started_at = time.time()
