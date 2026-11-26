from __future__ import annotations

from fastapi.testclient import TestClient

from ctf_workbench.api.main import create_app
from ctf_workbench.config import reset_settings_cache


def test_errors_use_the_envelope_and_request_id() -> None:
    reset_settings_cache()
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/no-such-route", headers={"X-Request-ID": "req-test-1"})
        assert response.status_code == 404
        body = response.json()
        assert body["error"]["code"] == "not_found"
        assert body["error"]["request_id"] == "req-test-1"
        assert "message" in body["error"]
        assert response.headers["x-request-id"] == "req-test-1"

        invalid = client.get("/api/v1/events", params={"stream_id": "x", "after_seq": -1})
        assert invalid.status_code == 422
        assert invalid.json()["error"]["code"] == "invalid_input"


def test_event_mutations_return_structured_405() -> None:
    reset_settings_cache()
    app = create_app()
    with TestClient(app) as client:
        response = client.post("/api/v1/events")
        assert response.status_code == 405
        assert response.json()["error"]["code"] == "method_not_allowed"
