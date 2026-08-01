from __future__ import annotations

from typing import cast

from vibe.cli.textual_ui.widgets.no_markup_static import NoMarkupStatic


class ModelDisplay(NoMarkupStatic):
    def __init__(self) -> None:
        super().__init__()
        self.can_focus = False

    def on_mount(self) -> None:
        self._update_display()

    def _update_display(self) -> None:
        pass

        # try:
        #     model = self.app.config.get_active_model()
        #     self.update(f" · {model.alias}[{model.thinking}]")
        # except ValueError:
        #     self.update("")

    def refresh_display(self) -> None:
        self._update_display()
