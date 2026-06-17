from __future__ import annotations

from pathlib import Path

import pytest

from vibe.core.paths._vibe_home import (
    _get_plans_dir,
    _get_session_log_dir,
    _get_vibe_home,
)


class TestGetPlansDir:
    @pytest.mark.skip(reason="Implemented custom plans and sessions folder structure")
    def test_returns_local_path_when_plans_dir_exists(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        plans_dir = tmp_path / ".vibe" / "plans"
        plans_dir.mkdir(parents=True)
        monkeypatch.chdir(tmp_path)
        result = _get_plans_dir()
        assert result == plans_dir

    @pytest.mark.skip(reason="Implemented custom plans and sessions folder structure")
    def test_returns_global_path_when_plans_dir_does_not_exist(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        global_plans = tmp_path / "global" / ".vibe" / "plans"
        global_plans.mkdir(parents=True)
        monkeypatch.setattr(
            "vibe.core.paths._vibe_home.VIBE_HOME",
            type("Mock", (), {"path": global_plans.parent})(),
        )
        result = _get_plans_dir()
        assert result == global_plans

    @pytest.mark.skip(reason="Implemented custom plans and sessions folder structure")
    def test_returns_global_path_when_plans_is_file_not_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / ".vibe").mkdir()
        (tmp_path / ".vibe" / "plans").write_text("")
        monkeypatch.chdir(tmp_path)
        global_plans = tmp_path / "global" / ".vibe" / "plans"
        global_plans.mkdir(parents=True)
        monkeypatch.setattr(
            "vibe.core.paths._vibe_home.VIBE_HOME",
            type("Mock", (), {"path": global_plans.parent})(),
        )
        result = _get_plans_dir()
        assert result == global_plans


class TestGetSessionLogDir:
    @pytest.mark.skip(reason="Implemented custom plans and sessions folder structure")
    def test_returns_local_path_when_session_log_dir_exists(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        session_dir = tmp_path / ".vibe" / "logs" / "session"
        session_dir.mkdir(parents=True)
        monkeypatch.chdir(tmp_path)
        result = _get_session_log_dir()
        assert result == session_dir

    @pytest.mark.skip(reason="Implemented custom plans and sessions folder structure")
    def test_returns_global_path_when_session_log_dir_does_not_exist(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        global_session = tmp_path / "global" / ".vibe" / "logs" / "session"
        global_session.mkdir(parents=True)
        monkeypatch.setattr(
            "vibe.core.paths._vibe_home.VIBE_HOME",
            type("Mock", (), {"path": global_session.parent.parent})(),
        )
        result = _get_session_log_dir()
        assert result == global_session

    @pytest.mark.skip(reason="Implemented custom plans and sessions folder structure")
    def test_returns_global_path_when_session_log_is_file_not_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / ".vibe" / "logs").mkdir(parents=True)
        (tmp_path / ".vibe" / "logs" / "session").write_text("")
        monkeypatch.chdir(tmp_path)
        global_session = tmp_path / "global" / ".vibe" / "logs" / "session"
        global_session.mkdir(parents=True)
        monkeypatch.setattr(
            "vibe.core.paths._vibe_home.VIBE_HOME",
            type("Mock", (), {"path": global_session.parent.parent})(),
        )
        result = _get_session_log_dir()
        assert result == global_session


class TestGetVibeHome:
    def test_returns_env_vibe_home(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        custom_vibe_home = tmp_path / "custom_vibe"
        monkeypatch.setenv("VIBE_HOME", str(custom_vibe_home))
        result = _get_vibe_home()
        assert result == custom_vibe_home


class TestGetPlansDirCurrent:
    def test_returns_vibe_home_plans_cwd_name_for_normal_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        vibe_home = tmp_path / ".vibe"
        vibe_home.mkdir()
        project_dir = tmp_path / "myproject"
        project_dir.mkdir()
        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            "vibe.core.paths._vibe_home.VIBE_HOME",
            type("Mock", (), {"path": vibe_home})(),
        )
        monkeypatch.setattr(
            "vibe.core.paths._vibe_home.is_dangerous_directory", lambda: (False, "")
        )
        result = _get_plans_dir()
        assert result == vibe_home / "plans" / "myproject"
        assert result.exists()

    def test_returns_vibe_home_plans_for_hidden_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        vibe_home = tmp_path / ".vibe"
        vibe_home.mkdir()
        hidden_dir = tmp_path / ".hidden"
        hidden_dir.mkdir()
        monkeypatch.chdir(hidden_dir)
        monkeypatch.setattr(
            "vibe.core.paths._vibe_home.VIBE_HOME",
            type("Mock", (), {"path": vibe_home})(),
        )
        result = _get_plans_dir()
        assert result == vibe_home / "plans"

    def test_returns_vibe_home_plans_for_dangerous_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        vibe_home = tmp_path / ".vibe"
        vibe_home.mkdir()
        dangerous_dir = tmp_path / "dangerous"
        dangerous_dir.mkdir()
        monkeypatch.chdir(dangerous_dir)
        monkeypatch.setattr(
            "vibe.core.paths._vibe_home.VIBE_HOME",
            type("Mock", (), {"path": vibe_home})(),
        )
        monkeypatch.setattr(
            "vibe.core.paths._vibe_home.is_dangerous_directory", lambda: (True, "")
        )
        result = _get_plans_dir()
        assert result == vibe_home / "plans"


class TestGetSessionLogDirCurrent:
    def test_returns_vibe_home_session_cwd_name_for_normal_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        vibe_home = tmp_path / ".vibe"
        vibe_home.mkdir()
        project_dir = tmp_path / "myproject"
        project_dir.mkdir()
        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            "vibe.core.paths._vibe_home.VIBE_HOME",
            type("Mock", (), {"path": vibe_home})(),
        )
        monkeypatch.setattr(
            "vibe.core.paths._vibe_home.is_dangerous_directory", lambda: (False, "")
        )
        result = _get_session_log_dir()
        assert result == vibe_home / "session" / "myproject"
        assert result.exists()

    def test_returns_vibe_home_session_for_hidden_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        vibe_home = tmp_path / ".vibe"
        vibe_home.mkdir()
        hidden_dir = tmp_path / ".hidden"
        hidden_dir.mkdir()
        monkeypatch.chdir(hidden_dir)
        monkeypatch.setattr(
            "vibe.core.paths._vibe_home.VIBE_HOME",
            type("Mock", (), {"path": vibe_home})(),
        )
        result = _get_session_log_dir()
        assert result == vibe_home / "session"

    def test_returns_vibe_home_session_for_dangerous_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        vibe_home = tmp_path / ".vibe"
        vibe_home.mkdir()
        dangerous_dir = tmp_path / "dangerous"
        dangerous_dir.mkdir()
        monkeypatch.chdir(dangerous_dir)
        monkeypatch.setattr(
            "vibe.core.paths._vibe_home.VIBE_HOME",
            type("Mock", (), {"path": vibe_home})(),
        )
        monkeypatch.setattr(
            "vibe.core.paths._vibe_home.is_dangerous_directory", lambda: (True, "")
        )
        result = _get_session_log_dir()
        assert result == vibe_home / "session"
