from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from ctf_workbench.db.models import Event, Outbox, utcnow
from ctf_workbench.services.events import OUTBOX_DESTINATION_UI

Publish = Callable[[Event], None]


def pending_rows(
    session: Session,
    *,
    destination: str = OUTBOX_DESTINATION_UI,
    limit: int = 50,
) -> list[Outbox]:
    rows = session.execute(
        select(Outbox)
        .where(
            Outbox.delivered_at.is_(None),
            Outbox.destination == destination,
            Outbox.available_at <= utcnow(),
        )
        .order_by(Outbox.available_at.asc(), Outbox.id.asc())
        .limit(limit)
    ).scalars()
    return list(rows)


def dispatch_pending(session: Session, publish: Publish, *, limit: int = 50) -> int:
    """Deliver at least once. Mark delivered only after publish returns."""
    delivered = 0
    for row in pending_rows(session, limit=limit):
        event = session.get(Event, row.event_id)
        row.attempts += 1
        if event is None:
            continue
        try:
            publish(event)
        except Exception:
            continue
        row.delivered_at = utcnow()
        delivered += 1
    session.flush()
    return delivered
