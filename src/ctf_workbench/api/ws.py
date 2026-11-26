from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ctf_workbench.api.events import EventRead
from ctf_workbench.config import get_settings
from ctf_workbench.db.engine import session_scope
from ctf_workbench.db.runtime import get_database
from ctf_workbench.services.broker import OVERFLOW, StreamBroker

router = APIRouter()
MAX_SEEN_IDS = 1000


def _broker(websocket: WebSocket) -> StreamBroker:
    return websocket.app.state.broker


def _origin_allowed(websocket: WebSocket) -> bool:
    origin = websocket.headers.get("origin")
    if origin is None:
        return True
    return origin in get_settings().cors_origin_list


@router.websocket("/api/v1/ws/events")
async def event_socket(websocket: WebSocket, stream_id: str, after_seq: int = 0) -> None:
    if not stream_id or after_seq < 0:
        await websocket.close(code=1008, reason="stream_id and after_seq>=0 are required")
        return
    if not _origin_allowed(websocket):
        await websocket.close(code=1008, reason="origin is not allowed")
        return

    await websocket.accept()
    broker = _broker(websocket)
    sub = broker.subscribe(stream_id)
    seen: list[str] = []
    seen_set: set[str] = set()
    try:
        db = get_database()
        with session_scope(db.sessions) as session:
            history = db.events.list_after(session, stream_id=stream_id, after_seq=after_seq)
        for event in history:
            payload = EventRead.model_validate(event).model_dump(mode="json")
            await websocket.send_json(payload)
            _remember(seen, seen_set, payload["id"])

        while True:
            payload = await sub.queue.get()
            if payload.get("error") == OVERFLOW:
                resume = payload.get("resume_seq")
                await websocket.close(code=1013, reason=f"slow consumer; resume_seq={resume}")
                return
            event_id = payload.get("id")
            if isinstance(event_id, str) and event_id in seen_set:
                continue
            await websocket.send_json(payload)
            if isinstance(event_id, str):
                _remember(seen, seen_set, event_id)
    except WebSocketDisconnect:
        return
    except asyncio.CancelledError:
        raise
    finally:
        broker.unsubscribe(sub)


def _remember(seen: list[str], seen_set: set[str], event_id: str) -> None:
    if event_id in seen_set:
        return
    seen.append(event_id)
    seen_set.add(event_id)
    if len(seen) > MAX_SEEN_IDS:
        old = seen.pop(0)
        seen_set.discard(old)
