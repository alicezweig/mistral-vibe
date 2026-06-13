from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from textual import events
from textual.app import ComposeResult
from textual.containers import Container, Grid
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView

from vibe.cli.textual_ui.pets import (
    DISABLED_PET_ID,
    Pet,
    get_all_available_pets,
    load_pet,
)
from vibe.cli.textual_ui.pets.image_protocol import PetImageSupport
from vibe.cli.textual_ui.pets.models import AmbientPet

if TYPE_CHECKING:
    from vibe.core.config import VibeConfig


class PetPickerScreen(ModalScreen[str | None]):
    """Modal screen for selecting and previewing pets."""

    CSS = """
    PetPickerScreen {
        align: center middle;
    }
    PetPickerScreen > Container {
        width: 80%;
        height: 80%;
        max-width: 1000px;
        max-height: 700px;
        border: rounded $primary;
        background: $surface;
    }
    PetPickerScreen > Container > Grid {
        height: 100%;
        width: 100%;
        grid-size: 2;
        grid-columns: 1fr 2fr;
        grid-rows: 1fr;
    }
    PetPickerScreen ListView {
        height: 100%;
        width: 100%;
        border: left $primary;
    }
    PetPickerScreen #preview-container {
        padding: 1 2;
        align: center middle;
        height: 100%;
        width: 100%;
    }
    PetPickerScreen #preview-image {
        height: auto;
        width: 100%;
        max-height: 100%;
    }
    PetPickerScreen Label.title {
        text-style: bold;
        text-align: center;
        padding: 1 0;
    }
    PetPickerScreen ListItem {
        height: auto;
    }
    PetPickerScreen ListItem Label.pet-name {
        padding: 0 1;
        width: 100%;
    }
    PetPickerScreen ListItem Label.pet-name.highlighted {
        background: $primary 20%;
    }
    PetPickerScreen .disabled-option {
        text-style: dim;
        color: $text-muted;
    }
    PetPickerScreen .hint {
        text-style: dim italic;
        text-align: center;
        padding: 1 0;
    }
    """

    def __init__(
        self,
        config: VibeConfig,
        cache_dir: Path,
        current_pet_id: str | None,
        on_select: Callable[[str | None], None],
    ):
        super().__init__()
        self.config = config
        self.cache_dir = cache_dir
        self.current_pet_id = current_pet_id
        self.on_select = on_select
        self._preview_pet: AmbientPet | None = None
        self._pets: list[Pet] = []

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Select a Pet", classes="title"),
            Grid(
                ListView(id="pet-list"),
                Container(id="preview-container"),
                id="main-grid",
            ),
            Label(
                "Use arrow keys to navigate, Enter to select, Esc to close",
                classes="hint",
            ),
            id="container",
        )

    def on_mount(self) -> None:
        list_view = self.query_one("#pet-list", ListView)
        preview_container = self.query_one("#preview-container", Container)

        # Load all available pets
        self._pets = get_all_available_pets(self.cache_dir)

        # Add disable option
        disable_item = ListItem(
            Label(
                "No Pet (disable)",
                id="pet-disabled",
                classes="disabled-option"
                if self.current_pet_id != DISABLED_PET_ID
                else "pet-name",
            ),
            id="pet-disabled",
        )
        list_view.append(disable_item)

        # Add each pet
        for pet in self._pets:
            pet_item = ListItem(
                Label(
                    f"{pet.display_name}",
                    id=f"pet-{pet.id}",
                    classes="pet-name",
                ),
                id=f"pet-{pet.id}",
            )
            list_view.append(pet_item)

        # Select current pet
        if self.current_pet_id == DISABLED_PET_ID:
            list_view.index = 0
            self._show_preview(None)
        else:
            for i, pet in enumerate(self._pets, start=1):
                if pet.id == self.current_pet_id:
                    list_view.index = i
                    self._show_preview(pet)
                    break

        # Check terminal support
        support = PetImageSupport.detect()
        if not support.is_supported:
            preview_container.mount(
                Label(
                    f"Pets not supported in this terminal\n{support.reason}",
                    classes="disabled-option",
                )
            )

    def _show_preview(self, pet: Pet | None) -> None:
        """Show preview of the selected pet."""
        preview_container = self.query_one("#preview-container", Container)
        preview_container.remove_children()

        if pet is None:
            preview_container.mount(Label("No pet selected", classes="hint"))
            return

        # Try to load the pet for preview
        if self.cache_dir:
            ambient_pet = load_pet(pet.id, self.cache_dir)
            if ambient_pet and ambient_pet.frames:
                # For preview, show the first frame
                # In a real implementation, we would animate the preview
                preview_container.mount(
                    Label(
                        f"Preview: {pet.display_name}\n{pet.description}",
                        classes="hint",
                    )
                )
                self._preview_pet = ambient_pet
            else:
                preview_container.mount(
                    Label(
                        f"Could not load preview for {pet.display_name}",
                        classes="disabled-option",
                    )
                )
        else:
            preview_container.mount(
                Label(
                    f"{pet.display_name}\n{pet.description}",
                    classes="hint",
                )
            )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item

        if item.id == "pet-disabled":
            self.on_select(DISABLED_PET_ID)
            self.dismiss()
            return

        if item.id and item.id.startswith("pet-"):
            pet_id = item.id[4:]
            self.on_select(pet_id)
            self.dismiss()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Update preview when hovering over pets."""
        item = event.item

        if item is None:
            return

        if item.id == "pet-disabled":
            self._show_preview(None)
            return

        if item.id and item.id.startswith("pet-"):
            pet_id = item.id[4:]
            for pet in self._pets:
                if pet.id == pet_id:
                    self._show_preview(pet)
                    break

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss()
