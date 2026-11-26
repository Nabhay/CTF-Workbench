from __future__ import annotations

import pytest
from pydantic import ValidationError

from ctf_workbench.config import Settings, reset_settings_cache


def test_rejects_short_session_secret(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("CTF_WORKBENCH_SESSION_SECRET", "too-short")
    monkeypatch.setenv("CTF_WORKBENCH_DATA_ROOT", str(tmp_path))
    reset_settings_cache()
    with pytest.raises(ValidationError) as exc:
        Settings()
    assert "at least 32 characters" in str(exc.value)


def test_rejects_nonlocal_bind_by_default(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("CTF_WORKBENCH_SESSION_SECRET", "t" * 32)
    monkeypatch.setenv("CTF_WORKBENCH_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("CTF_WORKBENCH_BIND_HOST", "0.0.0.0")
    monkeypatch.setenv("CTF_WORKBENCH_ALLOW_NONLOCAL_BIND", "false")
    reset_settings_cache()
    with pytest.raises(ValidationError) as exc:
        Settings()
    assert "not localhost" in str(exc.value)


def test_repr_hides_secret(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    secret = "super-secret-value-not-for-logs-ok"
    monkeypatch.setenv("CTF_WORKBENCH_SESSION_SECRET", secret)
    monkeypatch.setenv("CTF_WORKBENCH_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("CTF_WORKBENCH_DATABASE_URL", "sqlite:///./data/workbench.db")
    settings = Settings()
    dumped = repr(settings)
    assert secret not in dumped
    assert "session_secret" not in dumped


def test_redacts_database_password(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("CTF_WORKBENCH_SESSION_SECRET", "t" * 32)
    monkeypatch.setenv("CTF_WORKBENCH_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv(
        "CTF_WORKBENCH_DATABASE_URL",
        "postgresql://ctf:hunter2@127.0.0.1:5432/workbench",
    )
    settings = Settings()
    assert "hunter2" not in settings.redacted_database_url()
    assert "hunter2" not in repr(settings)
