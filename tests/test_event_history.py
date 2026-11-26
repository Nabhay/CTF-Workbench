from __future__ import annotations

from fastapi.testclient import TestClient

from ctf_workbench.api.main import create_app
from ctf_workbench.config import reset_settings_cache
from ctf_workbench.db.engine import session_scope
from ctf_workbench.db.runtime import get_database
from ctf_workbench.domain.ids import GLOBAL_STREAM_ID, LOCAL_ADMIN_ACTOR_ID


def test_event_history_is_ordered_and_cursorable() -> None:
    reset_settings_cache()
    app = create_app()
    with TestClient(app) as client:
        db = get_database()
        with session_scope(db.sessions) as session:
            db.events.append(
                session,
                actor_id=LOCAL_ADMIN_ACTOR_ID,
                type="probe.one",
                payload={"n": 1},
            )
            db.events.append(
                session,
                actor_id=LOCAL_ADMIN_ACTOR_ID,
                type="probe.two",
                payload={"n": 2},
            )

        first = client.get("/api/v1/events", params={"stream_id": GLOBAL_STREAM_ID, "limit": 2})
        assert first.status_code == 200
        body = first.json()
        types = [item["type"] for item in body["items"]]
        assert types[:2] == ["actor.bootstrapped", "probe.one"]
        assert [item["seq"] for item in body["items"]] == [1, 2]

        page = client.get(
            "/api/v1/events",
            params={"stream_id": GLOBAL_STREAM_ID, "after_seq": 2, "limit": 50},
        )
        assert page.status_code == 200
        rest = page.json()["items"]
        assert [item["type"] for item in rest] == ["probe.two"]
        assert rest[0]["seq"] == 3


def test_events_cannot_be_edited() -> None:
    reset_settings_cache()
    app = create_app()
    with TestClient(app) as client:
        for method in ("post", "put", "patch", "delete"):
            response = getattr(client, method)("/api/v1/events")
            assert response.status_code == 405


def test_unknown_stream_returns_empty_page() -> None:
    reset_settings_cache()
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/api/v1/events", params={"stream_id": "missing-stream"})
        assert response.status_code == 200
        body = response.json()
        assert body["items"] == []
        assert body["next_after_seq"] == 0
