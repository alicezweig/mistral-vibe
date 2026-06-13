from __future__ import annotations

from collections.abc import Callable
import os
from pathlib import Path

from vibe import VIBE_ROOT


class GlobalPath:
    def __init__(self, resolver: Callable[[], Path]) -> None:
        self._resolver = resolver

    @property
    def path(self) -> Path:
        return self._resolver()


_DEFAULT_VIBE_HOME = Path.home() / ".vibe"


def _get_vibe_home() -> Path:
    if vibe_home := os.getenv("VIBE_HOME"):
        return Path(vibe_home).expanduser().resolve()
    return _DEFAULT_VIBE_HOME


def _get_plans_dir() -> Path:
    return (
        (Path.cwd() / ".vibe" / "plans")
        if (Path.cwd() / ".vibe" / "plans").is_dir()
        else (VIBE_HOME.path / "plans")
    )


def _get_session_log_dir() -> Path:
    return (
        (Path.cwd() / ".vibe" / "session")
        if (Path.cwd() / ".vibe" / "session").is_dir()
        else (VIBE_HOME.path / "session")
    )


VIBE_HOME = GlobalPath(_get_vibe_home)
GLOBAL_ENV_FILE = GlobalPath(lambda: VIBE_HOME.path / ".env")
SESSION_LOG_DIR = GlobalPath(_get_session_log_dir)
TRUSTED_FOLDERS_FILE = GlobalPath(lambda: VIBE_HOME.path / "trusted_folders.toml")
LOG_DIR = GlobalPath(lambda: VIBE_HOME.path / "logs")
LOG_FILE = GlobalPath(lambda: VIBE_HOME.path / "logs" / "vibe.log")
CACHE_FILE = GlobalPath(lambda: VIBE_HOME.path / "cache.toml")
CACHE_DIR = GlobalPath(lambda: VIBE_HOME.path / "cache")
HISTORY_FILE = GlobalPath(lambda: VIBE_HOME.path / "vibehistory")
PLANS_DIR = GlobalPath(_get_plans_dir)

DEFAULT_TOOL_DIR = GlobalPath(lambda: VIBE_ROOT / "core" / "tools" / "builtins")
