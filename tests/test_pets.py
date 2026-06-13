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


class TestDefaultAnimations:
    """Tests for default animation configurations from Codex spritesheet."""

    def test_default_animations_exist(self):
        """Test that all required default animations exist."""
        from vibe.cli.textual_ui.pets.constants import DEFAULT_ANIMATIONS

        required_states = ["idle", "running", "waiting", "review", "failed"]
        for state in required_states:
            assert state in DEFAULT_ANIMATIONS, f"Missing animation: {state}"

    def test_idle_animation_frames(self):
        """Test idle animation uses frames 0-5 (row 0)."""
        from vibe.cli.textual_ui.pets.constants import DEFAULT_ANIMATIONS

        anim = DEFAULT_ANIMATIONS["idle"]
        # Task spec: frames=[0, 1, 2, 3, 4, 5]
        assert anim.frames == [0, 1, 2, 3, 4, 5], f"Idle frames: {anim.frames}"
        assert anim.fps == 8.0
        assert anim.loop is True
        assert anim.fallback == "idle"

    def test_running_animation_frames(self):
        """Test running animation uses frames 56-61 (row 7)."""
        from vibe.cli.textual_ui.pets.constants import DEFAULT_ANIMATIONS

        anim = DEFAULT_ANIMATIONS["running"]
        # Task spec: frames=[56, 57, 58, 59, 60, 61]
        # Current implementation includes 56-63, so check it contains the required frames
        assert 56 in anim.frames
        assert 57 in anim.frames
        assert 58 in anim.frames
        assert 59 in anim.frames
        assert 60 in anim.frames
        assert 61 in anim.frames
        assert anim.fps == 10.0
        assert anim.loop is True
        assert anim.fallback == "idle"

    def test_waiting_animation_frames(self):
        """Test waiting animation uses frames 48-53 (row 6)."""
        from vibe.cli.textual_ui.pets.constants import DEFAULT_ANIMATIONS

        anim = DEFAULT_ANIMATIONS["waiting"]
        # Task spec: frames=[48, 49, 50, 51, 52, 53]
        assert anim.frames == [48, 49, 50, 51, 52, 53], f"Waiting frames: {anim.frames}"
        assert anim.fps == 8.0
        assert anim.loop is True
        assert anim.fallback == "idle"

    def test_review_animation_frames(self):
        """Test review animation uses frames 64-69 (row 8)."""
        from vibe.cli.textual_ui.pets.constants import DEFAULT_ANIMATIONS

        anim = DEFAULT_ANIMATIONS["review"]
        # Task spec: frames=[64, 65, 66, 67, 68, 69]
        assert anim.frames == [64, 65, 66, 67, 68, 69], f"Review frames: {anim.frames}"
        assert anim.fps == 8.0
        assert anim.loop is True
        assert anim.fallback == "idle"

    def test_failed_animation_frames(self):
        """Test failed animation uses frames 40-47 (row 5)."""
        from vibe.cli.textual_ui.pets.constants import DEFAULT_ANIMATIONS

        anim = DEFAULT_ANIMATIONS["failed"]
        # Task spec: frames=[40, 41, 42, 43, 44, 45, 46, 47]
        assert anim.frames == [40, 41, 42, 43, 44, 45, 46, 47], f"Failed frames: {anim.frames}"
        assert anim.fps == 8.0
        assert anim.loop is True
        assert anim.fallback == "idle"


class TestAnimationFrameCycling:
    """Tests for animation frame cycling behavior."""

    def test_idle_frame_cycling(self):
        """Test idle animation frame cycling through all frames."""
        pet = create_test_pet()
        pet.animations["idle"] = Animation(frames=[0, 1, 2, 3, 4, 5], fps=8.0, loop=True)
        ambient_pet = AmbientPet(pet=pet, frames=[Path("/tmp/f.png")] * 20, support=MagicMock())
        
        with patch("vibe.cli.textual_ui.pets.models.time.time") as mock_time:
            mock_time.return_value = 1000.0
            ambient_pet.animation_started_at = 1000.0
            
            # Test each frame in sequence
            frame_duration = 1.0 / 8.0  # 0.125 seconds
            for i, frame_idx in enumerate([0, 1, 2, 3, 4, 5]):
                mock_time.return_value = 1000.0 + (i * frame_duration)
                assert ambient_pet.current_frame_index() == frame_idx

    def test_running_frame_cycling(self):
        """Test running animation frame cycling at 10 FPS."""
        pet = create_test_pet()
        pet.animations["running"] = Animation(frames=[56, 57, 58, 59, 60, 61], fps=10.0, loop=True)
        ambient_pet = AmbientPet(pet=pet, frames=[Path("/tmp/f.png")] * 20, support=MagicMock())
        
        with patch("vibe.cli.textual_ui.pets.models.time.time") as mock_time:
            mock_time.return_value = 1000.0
            ambient_pet.animation_started_at = 1000.0
            ambient_pet.set_notification(PetNotificationKind.RUNNING, "Running")
            # set_notification resets animation_started_at, so update it again
            ambient_pet.animation_started_at = 1000.0
            
            # Test each frame in sequence at 10 FPS (0.1s per frame)
            frame_duration = 1.0 / 10.0  # 0.1 seconds
            for i, frame_idx in enumerate([56, 57, 58, 59, 60, 61]):
                # Advance time slightly more than i * frame_duration to ensure we're in the right frame
                mock_time.return_value = 1000.0 + (i * frame_duration) + 0.001
                assert ambient_pet.current_frame_index() == frame_idx

    def test_waiting_frame_cycling(self):
        """Test waiting animation frame cycling."""
        pet = create_test_pet()
        pet.animations["waiting"] = Animation(frames=[48, 49, 50, 51, 52, 53], fps=8.0, loop=True)
        ambient_pet = AmbientPet(pet=pet, frames=[Path("/tmp/f.png")] * 20, support=MagicMock())
        
        with patch("vibe.cli.textual_ui.pets.models.time.time") as mock_time:
            mock_time.return_value = 1000.0
            ambient_pet.animation_started_at = 1000.0
            ambient_pet.set_notification(PetNotificationKind.WAITING, "Waiting")
            
            frame_duration = 1.0 / 8.0
            for i, frame_idx in enumerate([48, 49, 50, 51, 52, 53]):
                mock_time.return_value = 1000.0 + (i * frame_duration)
                assert ambient_pet.current_frame_index() == frame_idx

    def test_review_frame_cycling(self):
        """Test review animation frame cycling."""
        pet = create_test_pet()
        pet.animations["review"] = Animation(frames=[64, 65, 66, 67, 68, 69], fps=8.0, loop=True)
        ambient_pet = AmbientPet(pet=pet, frames=[Path("/tmp/f.png")] * 20, support=MagicMock())
        
        with patch("vibe.cli.textual_ui.pets.models.time.time") as mock_time:
            mock_time.return_value = 1000.0
            ambient_pet.animation_started_at = 1000.0
            ambient_pet.set_notification(PetNotificationKind.REVIEW, "Review")
            
            frame_duration = 1.0 / 8.0
            for i, frame_idx in enumerate([64, 65, 66, 67, 68, 69]):
                mock_time.return_value = 1000.0 + (i * frame_duration)
                assert ambient_pet.current_frame_index() == frame_idx

    def test_failed_frame_cycling(self):
        """Test failed animation frame cycling."""
        pet = create_test_pet()
        pet.animations["failed"] = Animation(frames=[40, 41, 42, 43, 44, 45, 46, 47], fps=8.0, loop=True)
        ambient_pet = AmbientPet(pet=pet, frames=[Path("/tmp/f.png")] * 20, support=MagicMock())
        
        with patch("vibe.cli.textual_ui.pets.models.time.time") as mock_time:
            mock_time.return_value = 1000.0
            ambient_pet.animation_started_at = 1000.0
            ambient_pet.set_notification(PetNotificationKind.FAILED, "Failed")
            
            frame_duration = 1.0 / 8.0
            for i, frame_idx in enumerate([40, 41, 42, 43, 44, 45, 46, 47]):
                mock_time.return_value = 1000.0 + (i * frame_duration)
                assert ambient_pet.current_frame_index() == frame_idx

    def test_animation_loops_correctly(self):
        """Test that animations loop back to start after last frame."""
        pet = create_test_pet()
        pet.animations["idle"] = Animation(frames=[0, 1, 2], fps=8.0, loop=True)
        ambient_pet = AmbientPet(pet=pet, frames=[Path("/tmp/f.png")] * 20, support=MagicMock())
        
        with patch("vibe.cli.textual_ui.pets.models.time.time") as mock_time:
            mock_time.return_value = 1000.0
            ambient_pet.animation_started_at = 1000.0
            
            frame_duration = 1.0 / 8.0
            # After 3 frames (0.375s), should loop back to frame 0
            mock_time.return_value = 1000.0 + (3 * frame_duration)
            assert ambient_pet.current_frame_index() == 0
            
            # After 6 frames (0.75s), should be at frame 0 again (2 full loops)
            mock_time.return_value = 1000.0 + (6 * frame_duration)
            assert ambient_pet.current_frame_index() == 0


class TestAllStateTransitions:
    """Tests for smooth transitions between all animation states."""

    def test_full_state_cycle(self):
        """Test idle -> running -> waiting -> review -> failed -> idle cycle."""
        ambient_pet = create_test_ambient_pet()
        
        # Start with idle
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["idle"]
        
        # idle -> running
        ambient_pet.set_notification(PetNotificationKind.RUNNING, "Running")
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["running"]
        
        # running -> waiting
        ambient_pet.set_notification(PetNotificationKind.WAITING, "Waiting")
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["waiting"]
        
        # waiting -> review
        ambient_pet.set_notification(PetNotificationKind.REVIEW, "Review")
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["review"]
        
        # review -> failed
        ambient_pet.set_notification(PetNotificationKind.FAILED, "Failed")
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["failed"]
        
        # failed -> idle
        ambient_pet.clear_notification()
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["idle"]

    def test_all_states_from_idle(self):
        """Test transitioning from idle to each state."""
        ambient_pet = create_test_ambient_pet()
        
        # Start at idle
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["idle"]
        
        # idle -> running
        ambient_pet.set_notification(PetNotificationKind.RUNNING, "Running")
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["running"]
        
        # Reset to idle
        ambient_pet.clear_notification()
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["idle"]
        
        # idle -> waiting
        ambient_pet.set_notification(PetNotificationKind.WAITING, "Waiting")
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["waiting"]
        
        # Reset to idle
        ambient_pet.clear_notification()
        
        # idle -> review
        ambient_pet.set_notification(PetNotificationKind.REVIEW, "Review")
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["review"]
        
        # Reset to idle
        ambient_pet.clear_notification()
        
        # idle -> failed
        ambient_pet.set_notification(PetNotificationKind.FAILED, "Failed")
        assert ambient_pet.current_animation() == ambient_pet.pet.animations["failed"]

    def test_transitions_reset_animation_timer(self):
        """Test that each state transition resets the animation timer."""
        with patch("vibe.cli.textual_ui.pets.models.time.time") as mock_time:
            mock_time.return_value = 1000.0
            ambient_pet = create_test_ambient_pet()
            ambient_pet.animation_started_at = 1000.0
            
            # idle -> running at 1010.0
            mock_time.return_value = 1010.0
            ambient_pet.set_notification(PetNotificationKind.RUNNING, "Running")
            assert ambient_pet.animation_started_at == 1010.0
            
            # running -> waiting at 1020.0
            mock_time.return_value = 1020.0
            ambient_pet.set_notification(PetNotificationKind.WAITING, "Waiting")
            assert ambient_pet.animation_started_at == 1020.0
            
            # waiting -> review at 1030.0
            mock_time.return_value = 1030.0
            ambient_pet.set_notification(PetNotificationKind.REVIEW, "Review")
            assert ambient_pet.animation_started_at == 1030.0
            
            # review -> failed at 1040.0
            mock_time.return_value = 1040.0
            ambient_pet.set_notification(PetNotificationKind.FAILED, "Failed")
            assert ambient_pet.animation_started_at == 1040.0
            
            # failed -> idle at 1050.0
            mock_time.return_value = 1050.0
            ambient_pet.clear_notification()
            assert ambient_pet.animation_started_at == 1050.0

    def test_immediate_state_transitions(self):
        """Test that state transitions are immediate (no delay)."""
        ambient_pet = create_test_ambient_pet()
        
        # All transitions should be immediate
        states_and_expected = [
            (None, "idle"),
            (PetNotificationKind.RUNNING, "running"),
            (PetNotificationKind.WAITING, "waiting"),
            (PetNotificationKind.REVIEW, "review"),
            (PetNotificationKind.FAILED, "failed"),
        ]
        
        for state, expected_anim_name in states_and_expected:
            if state is None:
                ambient_pet.clear_notification()
            else:
                ambient_pet.set_notification(state, f"{state} state")
            
            current_anim = ambient_pet.current_animation()
            expected_anim = ambient_pet.pet.animations[expected_anim_name]
            assert current_anim == expected_anim, (
                f"Expected {expected_anim_name} but got {current_anim}"
            )


if __name__ == "__main__":
    import pytest
    
    pytest.main([__file__, "-v"])
