from __future__ import annotations

from fastapi.testclient import TestClient

from ctf_workbench import __version__
from ctf_workbench.api.main import create_app
from ctf_workbench.config import get_settings, reset_settings_cache


def test_health_reports_live_settings() -> None:
    reset_settings_cache()
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["api"] == "ok"
    assert body["version"] == __version__
    settings = get_settings()
    assert body["bind"] == f"{settings.bind_host}:{settings.bind_port}"
    assert body["database"] == settings.redacted_database_url()
    assert body["worker"] == "separate_process"
