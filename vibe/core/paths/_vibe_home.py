from __future__ import annotations

from collections.abc import Callable
import os
from pathlib import Path

from vibe import VIBE_ROOT
from vibe.core.utils.paths import is_dangerous_directory


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
    cwd_name = Path.cwd().name
    default_plans_dir = VIBE_HOME.path / "plans"
    is_dangerous, _ = is_dangerous_directory()
    if cwd_name.startswith(".") or is_dangerous:
        return default_plans_dir
    plans_dir = VIBE_HOME.path / "plans" / cwd_name
    plans_dir.mkdir(parents=True, exist_ok=True)
    return plans_dir


def _get_session_log_dir() -> Path:
    cwd_name = Path.cwd().name
    default_session_log_dir = VIBE_HOME.path / "session"
    is_dangerous, _ = is_dangerous_directory()
    if cwd_name.startswith(".") or is_dangerous:
        return default_session_log_dir
    session_dir = VIBE_HOME.path / "session" / cwd_name
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


VIBE_HOME = GlobalPath(_get_vibe_home)
GLOBAL_ENV_FILE = GlobalPath(lambda: VIBE_HOME.path / ".env")
SESSION_LOG_DIR = GlobalPath(_get_session_log_dir)
WORKTREES_DIR = GlobalPath(lambda: VIBE_HOME.path / "worktrees")
TRUSTED_FOLDERS_FILE = GlobalPath(lambda: VIBE_HOME.path / "trusted_folders.toml")
LOG_DIR = GlobalPath(lambda: VIBE_HOME.path / "logs")
LOG_FILE = GlobalPath(lambda: VIBE_HOME.path / "logs" / "vibe.log")
CACHE_FILE = GlobalPath(lambda: VIBE_HOME.path / "cache.toml")
CONNECTOR_BOOTSTRAP_CACHE_FILE = GlobalPath(
    lambda: VIBE_HOME.path / "connector_bootstrap_cache.json"
)
HISTORY_FILE = GlobalPath(lambda: VIBE_HOME.path / "vibehistory")
PLANS_DIR = GlobalPath(_get_plans_dir)

DEFAULT_TOOL_DIR = GlobalPath(lambda: VIBE_ROOT / "core" / "tools" / "builtins")
