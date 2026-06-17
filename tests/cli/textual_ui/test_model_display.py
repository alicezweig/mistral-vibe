from __future__ import annotations

import pytest

from tests.conftest import build_test_vibe_app, build_test_vibe_config
from vibe.cli.textual_ui.widgets.model_display import ModelDisplay
from vibe.core.config._settings import ModelConfig


@pytest.mark.asyncio
async def test_model_display_shows_active_model_on_mount() -> None:
    """Test that ModelDisplay shows the active model when mounted."""
    config = build_test_vibe_config(
        models=[
            ModelConfig(
                name="test-model",
                provider="mistral",
                alias="test-model",
                thinking="off",
            )
        ],
        active_model="test-model",
    )
    app = build_test_vibe_app(config=config)
    async with app.run_test() as pilot:
        await pilot.pause()
        model_display = app.query_one(ModelDisplay)
        # Should show model with thinking level
        assert "test-model[off]" in str(model_display.content)


@pytest.mark.asyncio
async def test_model_display_updates_on_model_change() -> None:
    """Test that ModelDisplay updates when active model changes."""
    config = build_test_vibe_config(
        models=[
            ModelConfig(
                name="model-1", provider="mistral", alias="model-1", thinking="off"
            ),
            ModelConfig(
                name="model-2", provider="mistral", alias="model-2", thinking="off"
            ),
        ],
        active_model="model-1",
    )
    app = build_test_vibe_app(config=config)
    async with app.run_test() as pilot:
        await pilot.pause()
        model_display = app.query_one(ModelDisplay)

        # Initial state
        assert "model-1[off]" in str(model_display.content)

        app.config.active_model = "model-2"

        # Refresh display
        model_display.refresh_display()

        # Should now show new model
        assert "model-2[off]" in str(model_display.content)
        assert "model-1" not in str(model_display.content)


@pytest.mark.asyncio
async def test_model_display_updates_on_thinking_level_change() -> None:
    """Test that ModelDisplay updates when thinking level changes."""
    config = build_test_vibe_config(
        models=[
            ModelConfig(
                name="model-1", provider="mistral", alias="model-1", thinking="off"
            )
        ],
        active_model="model-1",
    )
    app = build_test_vibe_app(config=config)
    async with app.run_test() as pilot:
        await pilot.pause()
        model_display = app.query_one(ModelDisplay)

        # Initial state with off thinking
        assert "model-1[off]" in str(model_display.content)

        # Change thinking level in active model
        app.config.set_thinking("max")

        # Refresh display
        model_display.refresh_display()

        # Should now show max thinking
        assert "model-1[max]" in str(model_display.content)
        assert "[off]" not in str(model_display.content)
