#!/usr/bin/env python3
"""Tests for the pet notification system in AmbientPet."""

from __future__ import annotations

from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vibe.cli.textual_ui.pets.models import (
    AmbientPet,
    Animation,
    Pet,
    PetNotification,
    PetNotificationKind,
)


def create_test_pet() -> Pet:
    """Create a test pet with required animations."""
    return Pet(
        id="test_pet",
        display_name="Test Pet",
        description="Test pet for notifications",
        spritesheet_path=Path("/tmp/test_pet.png"),
        frame_width=192,
        frame_height=208,
        columns=8,
        rows=9,
        animations={
            "idle": Animation(frames=[0, 1, 2], fps=8.0, loop=True),
            "running": Animation(frames=[3, 4, 5], fps=8.0, loop=True),
            "waiting": Animation(frames=[6, 7, 8], fps=8.0, loop=True),
            "review": Animation(frames=[9, 10, 11], fps=8.0, loop=True),
            "failed": Animation(frames=[12, 13, 14], fps=8.0, loop=True),
        },
    )


def create_test_ambient_pet() -> AmbientPet:
    """Create a test AmbientPet with mock support."""
    pet = create_test_pet()
    mock_support = MagicMock()
    frames = [Path(f"/tmp/frame_{i}.png") for i in range(20)]
    return AmbientPet(pet=pet, frames=frames, support=mock_support)


class TestPetNotificationKind:
    """Tests for PetNotificationKind enum."""

    def test_notification_kind_values(self):
        """Test that notification kinds have correct string values."""
        assert PetNotificationKind.RUNNING == "running"
        assert PetNotificationKind.WAITING == "waiting"
        assert PetNotificationKind.REVIEW == "review"
        assert PetNotificationKind.FAILED == "failed"


class TestPetNotification:
    """Tests for PetNotification class."""

    def test_notification_creation(self):
        """Test creating a notification with kind and body."""
        notification = PetNotification(PetNotificationKind.RUNNING, "Test message")
        assert notification.kind == PetNotificationKind.RUNNING
        assert notification.body == "Test message"
        assert notification.created_at is not None

    def test_notification_creation_without_body(self):
        """Test creating a notification without body."""
        notification = PetNotification(PetNotificationKind.WAITING, None)
        assert notification.kind == PetNotificationKind.WAITING
        assert notification.body is None

    def test_running_notification_lifetime(self):
        """Test RUNNING notification lifetime is 180 seconds."""
        assert PetNotification.RUNNING_LIFETIME == 180

    def test_failed_notification_lifetime(self):
        """Test FAILED notification lifetime is 3600 seconds."""
        assert PetNotification.FAILED_LIFETIME == 3600

    def test_waiting_notification_lifetime(self):
        """Test WAITING notification lifetime is 86400 seconds."""
        assert PetNotification.WAITING_LIFETIME == 86400

    def test_review_notification_lifetime(self):
        """Test REVIEW notification lifetime is 604800 seconds."""
        assert PetNotification.REVIEW_LIFETIME == 604800

    def test_notification_not_expired_when_fresh(self):
        """Test that fresh notifications are not expired."""
        notification = PetNotification(PetNotificationKind.RUNNING, "Fresh")
        assert not notification.is_expired()

    def test_notification_expired_after_lifetime(self):
        """Test that notifications expire after their lifetime."""
        notification = PetNotification(PetNotificationKind.RUNNING, "Old")
        # Mock time.time to be in the future
        with patch("vibe.cli.textual_ui.pets.models.time.time") as mock_time:
            mock_time.return_value = notification.created_at + 200  # 200 seconds later
            assert notification.is_expired()

    def test_notification_not_expired_before_lifetime(self):
        """Test that notifications don't expire before their lifetime."""
        notification = PetNotification(PetNotificationKind.RUNNING, "Still good")
        with patch("vibe.cli.textual_ui.pets.models.time.time") as mock_time:
            mock_time.return_value = notification.created_at + 100  # 100 seconds later
            assert not notification.is_expired()

    def test_notification_label_mapping(self):
        """Test notification labels are correct."""
        assert PetNotification(
            PetNotificationKind.RUNNING, ""
        ).label == "Running"
        assert PetNotification(
            PetNotificationKind.WAITING, ""
        ).label == "Needs input"
        assert PetNotification(PetNotificationKind.REVIEW, "").label == "Ready"
        assert PetNotification(PetNotificationKind.FAILED, "").label == "Blocked"


class TestAmbientPetNotificationSystem:
    """Tests for AmbientPet notification system."""

    def test_default_state_is_idle(self):
        """Test that default state (no notification) returns idle animation."""
        ambient_pet = create_test_ambient_pet()
        anim = ambient_pet.current_animation()
        assert anim == ambient_pet.pet.animations["idle"]

    def test_set_notification_running(self):
        """Test setting RUNNING notification."""
        ambient_pet = create_test_ambient_pet()
        ambient_pet.set_notification(PetNotificationKind.RUNNING, "Running task")
        assert ambient_pet.notification is not None
        assert ambient_pet.notification.kind == PetNotificationKind.RUNNING
        assert ambient_pet.notification.body == "Running task"

    def test_set_notification_waiting(self):
        """Test setting WAITING notification."""
        ambient_pet = create_test_ambient_pet()
        ambient_pet.set_notification(PetNotificationKind.WAITING, "Need input")
        assert ambient_pet.notification is not None
        assert ambient_pet.notification.kind == PetNotificationKind.WAITING
        assert ambient_pet.notification.body == "Need input"

    def test_set_notification_review(self):
        """Test setting REVIEW notification."""
        ambient_pet = create_test_ambient_pet()
        ambient_pet.set_notification(PetNotificationKind.REVIEW, "Ready for review")
        assert ambient_pet.notification is not None
        assert ambient_pet.notification.kind == PetNotificationKind.REVIEW

    def test_set_notification_failed(self):
        """Test setting FAILED notification."""
        ambient_pet = create_test_ambient_pet()
        ambient_pet.set_notification(PetNotificationKind.FAILED, "Error occurred")
        assert ambient_pet.notification is not None
        assert ambient_pet.notification.kind == PetNotificationKind.FAILED

    def test_clear_notification(self):
        """Test clearing notification returns to idle."""
        ambient_pet = create_test_ambient_pet()
        ambient_pet.set_notification(PetNotificationKind.RUNNING, "Running")
        assert ambient_pet.notification is not None
        
        ambient_pet.clear_notification()
        assert ambient_pet.notification is None

    def test_current_animation_mapping_running(self):
        """Test that RUNNING notification maps to running animation."""
        ambient_pet = create_test_ambient_pet()
        ambient_pet.set_notification(PetNotificationKind.RUNNING, "Running")
        anim = ambient_pet.current_animation()
        assert anim == ambient_pet.pet.animations["running"]

    def test_current_animation_mapping_waiting(self):
        """Test that WAITING notification maps to waiting animation."""
        ambient_pet = create_test_ambient_pet()
        ambient_pet.set_notification(PetNotificationKind.WAITING, "Waiting")
        anim = ambient_pet.current_animation()
        assert anim == ambient_pet.pet.animations["waiting"]

    def test_current_animation_mapping_review(self):
        """Test that REVIEW notification maps to review animation."""
        ambient_pet = create_test_ambient_pet()
        ambient_pet.set_notification(PetNotificationKind.REVIEW, "Review")
        anim = ambient_pet.current_animation()
        assert anim == ambient_pet.pet.animations["review"]

    def test_current_animation_mapping_failed(self):
        """Test that FAILED notification maps to failed animation."""
        ambient_pet = create_test_ambient_pet()
        ambient_pet.set_notification(PetNotificationKind.FAILED, "Failed")
        anim = ambient_pet.current_animation()
        assert anim == ambient_pet.pet.animations["failed"]

    def test_current_animation_returns_idle_when_notification_expired(self):
        """Test that expired notification returns to idle animation."""
        ambient_pet = create_test_ambient_pet()
        ambient_pet.animation_started_at = 1000.0
        
        # Create notification with a specific creation time
        with patch("vibe.cli.textual_ui.pets.models.time.time") as mock_time:
            mock_time.return_value = 1000.0
            ambient_pet.set_notification(PetNotificationKind.RUNNING, "Running")
            # Manually set the notification's created_at
            assert ambient_pet.notification is not None
            ambient_pet.notification.created_at = 1000.0
            
            # Now set time to be past the RUNNING_LIFETIME (180 seconds)
            mock_time.return_value = 1000.0 + 200  # 200 seconds later
            anim = ambient_pet.current_animation()
            assert anim == ambient_pet.pet.animations["idle"]

    def test_set_notification_resets_animation_timer(self):
        """Test that set_notification resets the animation timer."""
        with patch("vibe.cli.textual_ui.pets.models.time.time") as mock_time:
            mock_time.return_value = 1000.0
            ambient_pet = create_test_ambient_pet()
            ambient_pet.animation_started_at = 1000.0
            original_time = ambient_pet.animation_started_at
            
            # Set notification at a later time
            mock_time.return_value = 1010.0
            ambient_pet.set_notification(PetNotificationKind.RUNNING, "Running")
            # animation_started_at should be updated to current time
            assert ambient_pet.animation_started_at == 1010.0
            assert ambient_pet.animation_started_at > original_time

    def test_clear_notification_resets_animation_timer(self):
        """Test that clear_notification resets the animation timer."""
        with patch("vibe.cli.textual_ui.pets.models.time.time") as mock_time:
            mock_time.return_value = 1000.0
            ambient_pet = create_test_ambient_pet()
            ambient_pet.animation_started_at = 1000.0
            ambient_pet.set_notification(PetNotificationKind.RUNNING, "Running")
            original_time = ambient_pet.animation_started_at
            
            # Clear notification at a later time
            mock_time.return_value = 1010.0
            ambient_pet.clear_notification()
            assert ambient_pet.animation_started_at == 1010.0
            assert ambient_pet.animation_started_at > original_time


class TestAmbientPetCurrentFrameIndex:
    """Tests for AmbientPet current_frame_index method."""

    def test_current_frame_index_basic(self):
        """Test basic frame index calculation."""
        with patch("vibe.cli.textual_ui.pets.models.time.time") as mock_time:
            mock_time.return_value = 1000.0
            ambient_pet = create_test_ambient_pet()
            # Reset animation_started_at to use mocked time
            ambient_pet.animation_started_at = 1000.0
            # Idle animation has frames [0, 1, 2] at 8 fps
            # At time 0, should return first frame
            frame_idx = ambient_pet.current_frame_index()
            assert frame_idx == 0  # First frame of idle animation

    def test_current_frame_index_with_elapsed_time(self):
        """Test frame index calculation with elapsed time."""
        with patch("vibe.cli.textual_ui.pets.models.time.time") as mock_time:
            mock_time.return_value = 1000.0
            ambient_pet = create_test_ambient_pet()
            ambient_pet.animation_started_at = 1000.0
            ambient_pet.set_notification(PetNotificationKind.RUNNING, "Running")
            # Running animation has frames [3, 4, 5] at 8 fps
            # frame_duration = 1/8 = 0.125 seconds
            
            # 0.25 seconds later -> idx = 0.25/0.125 = 2 -> frames[2] = 5
            mock_time.return_value = 1000.25
            frame_idx = ambient_pet.current_frame_index()
            assert frame_idx == 5

    def test_current_frame_index_with_loop_start(self):
        """Test frame index calculation with loop_start parameter."""
        with patch("vibe.cli.textual_ui.pets.models.time.time") as mock_time:
            mock_time.return_value = 1000.0
            # Create a pet with animation that has loop_start
            pet = create_test_pet()
            pet.animations["running"] = Animation(
                frames=[3, 4, 5, 6, 7], fps=8.0, loop=True, loop_start=2
            )
            ambient_pet = AmbientPet(pet=pet, frames=[Path("/tmp/f.png")] * 10, support=MagicMock())
            ambient_pet.animation_started_at = 1000.0
            ambient_pet.set_notification(PetNotificationKind.RUNNING, "Running")
            
            # At time 0, should return first frame (index 2 in frames, which is value 5)
            frame_idx = ambient_pet.current_frame_index()
            assert frame_idx == 5  # frames[2] = 5


class TestAmbientPetStateTransitions:
    """Tests for AmbientPet state transitions."""

    def test_transition_idle_to_running_to_idle(self):
        """Test idle -> running -> idle transition."""
        ambient_pet = create_test_ambient_pet()
        
        # Start with idle
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["idle"]
        
        # Set to running
        ambient_pet.set_notification(PetNotificationKind.RUNNING, "Running")
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["running"]
        
        # Clear back to idle
        ambient_pet.clear_notification()
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["idle"]

    def test_transition_idle_to_waiting_to_idle(self):
        """Test idle -> waiting -> idle transition."""
        ambient_pet = create_test_ambient_pet()
        
        # Start with idle
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["idle"]
        
        # Set to waiting
        ambient_pet.set_notification(PetNotificationKind.WAITING, "Waiting")
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["waiting"]
        
        # Clear back to idle
        ambient_pet.clear_notification()
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["idle"]

    def test_transition_idle_to_review_to_idle(self):
        """Test idle -> review -> idle transition."""
        ambient_pet = create_test_ambient_pet()
        
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["idle"]
        ambient_pet.set_notification(PetNotificationKind.REVIEW, "Review")
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["review"]
        ambient_pet.clear_notification()
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["idle"]

    def test_transition_idle_to_failed_to_idle(self):
        """Test idle -> failed -> idle transition."""
        ambient_pet = create_test_ambient_pet()
        
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["idle"]
        ambient_pet.set_notification(PetNotificationKind.FAILED, "Failed")
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["failed"]
        ambient_pet.clear_notification()
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["idle"]


if __name__ == "__main__":
    import pytest
    
    pytest.main([__file__, "-v"])
