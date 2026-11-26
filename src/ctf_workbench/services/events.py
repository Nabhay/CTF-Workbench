from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ctf_workbench.db.models import Event, EventStream, Outbox, utcnow
from ctf_workbench.domain.ids import GLOBAL_STREAM_ID, new_id
from ctf_workbench.domain.pagination import clamp_page_size

OUTBOX_DESTINATION_UI = "ui.events"


class EventService:
    """Append-only events. Must run inside the caller's open transaction."""

    def append(
        self,
        session: Session,
        *,
        actor_id: str,
        type: str,
        payload: dict[str, Any],
        challenge_id: str | None = None,
        stream_id: str | None = None,
        correlation_id: str | None = None,
        schema_version: int = 1,
        event_id: str | None = None,
        destination: str = OUTBOX_DESTINATION_UI,
    ) -> Event:
        resolved_stream = stream_id or (challenge_id if challenge_id else GLOBAL_STREAM_ID)
        seq = self._next_seq(session, resolved_stream)
        event = Event(
            id=event_id or new_id(),
            stream_id=resolved_stream,
            seq=seq,
            ts=utcnow(),
            actor_id=actor_id,
            challenge_id=challenge_id,
            type=type,
            schema_version=schema_version,
            payload_json=payload,
            correlation_id=correlation_id,
        )
        session.add(event)
        session.add(
            Outbox(
                id=new_id(),
                event_id=event.id,
                destination=destination,
                payload_json={"event_id": event.id, "type": type, "stream_id": resolved_stream, "seq": seq},
                available_at=event.ts,
            )
        )
        session.flush()
        return event

    def list_after(
        self,
        session: Session,
        *,
        stream_id: str,
        after_seq: int = 0,
        limit: int | None = None,
    ) -> list[Event]:
        if after_seq < 0:
            raise ValueError("after_seq must be >= 0")
        size = clamp_page_size(limit)
        rows = session.execute(
            select(Event)
            .where(Event.stream_id == stream_id, Event.seq > after_seq)
            .order_by(Event.seq.asc())
            .limit(size)
        ).scalars()
        return list(rows)

    def _next_seq(self, session: Session, stream_id: str) -> int:
        stream = session.execute(
            select(EventStream).where(EventStream.stream_id == stream_id).with_for_update()
        ).scalar_one_or_none()
        if stream is None:
            stream = EventStream(stream_id=stream_id, next_seq=2)
            session.add(stream)
            session.flush()
            return 1
        seq = stream.next_seq
        stream.next_seq = seq + 1
        return seq
