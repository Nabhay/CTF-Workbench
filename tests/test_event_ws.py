from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from ctf_workbench.api.events import EventRead
from ctf_workbench.api.main import create_app
from ctf_workbench.config import reset_settings_cache
from ctf_workbench.db.engine import session_scope
from ctf_workbench.db.runtime import get_database
from ctf_workbench.domain.ids import GLOBAL_STREAM_ID, LOCAL_ADMIN_ACTOR_ID


def _payload(event: object) -> dict:
    return EventRead.model_validate(event).model_dump(mode="json")


def test_ws_replays_history_then_live_in_order() -> None:
    reset_settings_cache()
    app = create_app()
    with TestClient(app) as client:
        with client.websocket_connect(f"/api/v1/ws/events?stream_id={GLOBAL_STREAM_ID}&after_seq=0") as ws:
            boot = ws.receive_json()
            assert boot["type"] == "actor.bootstrapped"
            db = get_database()
            with session_scope(db.sessions) as session:
                first = db.events.append(
                    session, actor_id=LOCAL_ADMIN_ACTOR_ID, type="live.one", payload={}
                )
                second = db.events.append(
                    session, actor_id=LOCAL_ADMIN_ACTOR_ID, type="live.two", payload={}
                )
                p1, p2 = _payload(first), _payload(second)
            app.state.broker.publish(p1)
            app.state.broker.publish(p2)
            assert ws.receive_json()["type"] == "live.one"
            two = ws.receive_json()
            assert two["type"] == "live.two"
            last_seq = two["seq"]

        with client.websocket_connect(
            f"/api/v1/ws/events?stream_id={GLOBAL_STREAM_ID}&after_seq={last_seq}"
        ) as ws:
            db = get_database()
            with session_scope(db.sessions) as session:
                third = db.events.append(
                    session, actor_id=LOCAL_ADMIN_ACTOR_ID, type="live.three", payload={}
                )
                p3 = _payload(third)
            app.state.broker.publish(p3)
            nxt = ws.receive_json()
            assert nxt["type"] == "live.three"
            assert nxt["seq"] == last_seq + 1


def test_ws_deduplicates_event_ids() -> None:
    reset_settings_cache()
    app = create_app()
    with TestClient(app) as client:
        with client.websocket_connect(f"/api/v1/ws/events?stream_id={GLOBAL_STREAM_ID}&after_seq=0") as ws:
            ws.receive_json()
            db = get_database()
            with session_scope(db.sessions) as session:
                event = db.events.append(
                    session, actor_id=LOCAL_ADMIN_ACTOR_ID, type="dup", payload={}
                )
                extra = db.events.append(
                    session, actor_id=LOCAL_ADMIN_ACTOR_ID, type="after-dup", payload={}
                )
                payload = _payload(event)
                extra_payload = _payload(extra)
            app.state.broker.publish(payload)
            app.state.broker.publish(payload)
            app.state.broker.publish(extra_payload)
            assert ws.receive_json()["type"] == "dup"
            assert ws.receive_json()["type"] == "after-dup"


def test_ws_rejects_disallowed_origin() -> None:
    reset_settings_cache()
    app = create_app()
    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect(
                f"/api/v1/ws/events?stream_id={GLOBAL_STREAM_ID}",
                headers={"Origin": "http://evil.example"},
            ):
                pass
        assert exc.value.code == 1008
