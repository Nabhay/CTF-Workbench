from __future__ import annotations

import os
from collections.abc import Iterator

import pytest


def pytest_configure(config: pytest.Config) -> None:
    os.environ.setdefault("CTF_WORKBENCH_SESSION_SECRET", "test-secret-not-for-production-use-ok")
    os.environ.setdefault("CTF_WORKBENCH_BIND_HOST", "127.0.0.1")
    os.environ.setdefault("CTF_WORKBENCH_BIND_PORT", "8745")
    os.environ.setdefault("CTF_WORKBENCH_ALLOW_NONLOCAL_BIND", "false")


@pytest.fixture(autouse=True)
def _migrated_database(tmp_path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    from ctf_workbench.config import get_settings, reset_settings_cache
    from ctf_workbench.db.migrations import upgrade_to_head
    from ctf_workbench.db.runtime import reset_database

    db_path = tmp_path / "test.db"
    monkeypatch.setenv("CTF_WORKBENCH_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("CTF_WORKBENCH_DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    reset_settings_cache()
    reset_database()
    upgrade_to_head(get_settings().database_url)
    yield
    reset_database()
    reset_settings_cache()
