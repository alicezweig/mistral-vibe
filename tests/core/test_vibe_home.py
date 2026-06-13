from __future__ import annotations

from pathlib import Path

import pytest

from vibe.core.paths._vibe_home import _get_plans_dir, _get_session_log_dir


class TestGetPlansDir:
    def test_returns_local_path_when_plans_dir_exists(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        plans_dir = tmp_path / ".vibe" / "plans"
        plans_dir.mkdir(parents=True)
        monkeypatch.chdir(tmp_path)
        result = _get_plans_dir()
        assert result == plans_dir

    def test_returns_global_path_when_plans_dir_does_not_exist(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        global_plans = tmp_path / "global" / ".vibe" / "plans"
        global_plans.mkdir(parents=True)
        monkeypatch.setattr(
            "vibe.core.paths._vibe_home.VIBE_HOME", type("Mock", (), {"path": global_plans.parent})()
        )
        result = _get_plans_dir()
        assert result == global_plans

    def test_returns_global_path_when_plans_is_file_not_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / ".vibe").mkdir()
        (tmp_path / ".vibe" / "plans").write_text("")
        monkeypatch.chdir(tmp_path)
        global_plans = tmp_path / "global" / ".vibe" / "plans"
        global_plans.mkdir(parents=True)
        monkeypatch.setattr(
            "vibe.core.paths._vibe_home.VIBE_HOME", type("Mock", (), {"path": global_plans.parent})()
        )
        result = _get_plans_dir()
        assert result == global_plans


class TestGetSessionLogDir:
    def test_returns_local_path_when_session_log_dir_exists(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        session_dir = tmp_path / ".vibe" / "logs" / "session"
        session_dir.mkdir(parents=True)
        monkeypatch.chdir(tmp_path)
        result = _get_session_log_dir()
        assert result == session_dir

    def test_returns_global_path_when_session_log_dir_does_not_exist(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        global_session = tmp_path / "global" / ".vibe" / "logs" / "session"
        global_session.mkdir(parents=True)
        monkeypatch.setattr(
            "vibe.core.paths._vibe_home.VIBE_HOME", type("Mock", (), {"path": global_session.parent.parent})()
        )
        result = _get_session_log_dir()
        assert result == global_session

    def test_returns_global_path_when_session_log_is_file_not_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / ".vibe" / "logs").mkdir(parents=True)
        (tmp_path / ".vibe" / "logs" / "session").write_text("")
        monkeypatch.chdir(tmp_path)
        global_session = tmp_path / "global" / ".vibe" / "logs" / "session"
        global_session.mkdir(parents=True)
        monkeypatch.setattr(
            "vibe.core.paths._vibe_home.VIBE_HOME", type("Mock", (), {"path": global_session.parent.parent})()
        )
        result = _get_session_log_dir()
        assert result == global_session
