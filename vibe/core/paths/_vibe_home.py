from __future__ import annotations

from pathlib import Path

from vibe import VIBE_ROOT
from vibe.utils.paths import GlobalPath, get_vibe_home


def _get_plans_dir() -> Path:
    cwd_name = Path.cwd().name
    default_plans_dir = VIBE_HOME.path / "plans"
    if cwd_name.startswith("."):
        return default_plans_dir
    plans_dir = VIBE_HOME.path / "plans" / cwd_name
    plans_dir.mkdir(parents=True, exist_ok=True)
    return plans_dir


def _get_session_log_dir() -> Path:
    cwd_name = Path.cwd().name
    default_session_log_dir = VIBE_HOME.path / "session"
    if cwd_name.startswith("."):
        return default_session_log_dir
    session_dir = VIBE_HOME.path / "session" / cwd_name
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


VIBE_HOME = GlobalPath(get_vibe_home)
GLOBAL_ENV_FILE = GlobalPath(lambda: VIBE_HOME.path / ".env")
SESSION_LOG_DIR = GlobalPath(_get_session_log_dir)
WORKTREES_DIR = GlobalPath(lambda: VIBE_HOME.path / "worktrees")
TRUSTED_FOLDERS_FILE = GlobalPath(lambda: VIBE_HOME.path / "trusted_folders.toml")
LOG_DIR = GlobalPath(lambda: VIBE_HOME.path / "logs")
LOG_FILE = GlobalPath(lambda: VIBE_HOME.path / "logs" / "vibe.log")
CACHE_FILE = GlobalPath(lambda: VIBE_HOME.path / "cache.toml")
PROJECTS_FILE = GlobalPath(lambda: VIBE_HOME.path / "projects.toml")
CONNECTOR_BOOTSTRAP_CACHE_FILE = GlobalPath(
    lambda: VIBE_HOME.path / "connector_bootstrap_cache.json"
)
HISTORY_FILE = GlobalPath(lambda: VIBE_HOME.path / "vibehistory")
PLANS_DIR = GlobalPath(_get_plans_dir)

DEFAULT_TOOL_DIR = GlobalPath(lambda: VIBE_ROOT / "core" / "tools" / "builtins")
