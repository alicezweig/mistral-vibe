"""Textual messages for pet state changes.

These custom messages allow decoupled communication between the agent loop
and the pet widget, enabling pet animations to respond to application state changes.
"""
from __future__ import annotations

from textual.message import Message

from vibe.cli.textual_ui.pets.models import PetNotificationKind


class PetSetNotification(Message):
    """Message to set pet notification state.
    
    This message triggers the pet to switch to a specific animation
    based on the application state (RUNNING, WAITING, REVIEW, FAILED).
    """

    def __init__(
        self, kind: PetNotificationKind, body: str | None = None
    ) -> None:
        super().__init__()
        self.kind = kind
        self.body = body


class PetClearNotification(Message):
    """Message to clear pet notification (return to idle).
    
    This message triggers the pet to return to its default idle animation.
    """

    pass
