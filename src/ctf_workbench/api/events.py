from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from ctf_workbench.db.engine import session_scope
from ctf_workbench.db.runtime import get_database

router = APIRouter()


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    stream_id: str
    seq: int
    ts: datetime
    actor_id: str
    challenge_id: str | None
    type: str
    schema_version: int
    payload_json: dict[str, Any]
    correlation_id: str | None


class EventListResponse(BaseModel):
    stream_id: str
    after_seq: int
    items: list[EventRead]
    next_after_seq: int = Field(description="Pass as after_seq to fetch the next page.")


@router.get("/api/v1/events", response_model=EventListResponse)
def list_events(
    stream_id: str = Query(min_length=1, max_length=64),
    after_seq: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None, ge=1, le=200),
) -> EventListResponse:
    db = get_database()
    with session_scope(db.sessions) as session:
        items = db.events.list_after(
            session, stream_id=stream_id, after_seq=after_seq, limit=limit
        )
        next_seq = items[-1].seq if items else after_seq
        return EventListResponse(
            stream_id=stream_id,
            after_seq=after_seq,
            items=[EventRead.model_validate(item) for item in items],
            next_after_seq=next_seq,
        )


@router.api_route("/api/v1/events", methods=["POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
def events_are_append_only() -> None:
    raise HTTPException(
        status_code=405,
        detail="Events cannot be edited through public APIs. Append happens only inside a service transaction.",
    )
