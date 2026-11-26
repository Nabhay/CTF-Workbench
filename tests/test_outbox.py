from __future__ import annotations

from ctf_workbench.config import get_settings
from ctf_workbench.db.engine import create_engine_from_url, session_factory, session_scope
from ctf_workbench.db.models import Actor, Event, Outbox
from ctf_workbench.domain.enums import ActorKind
from ctf_workbench.domain.ids import new_id
from ctf_workbench.services.events import EventService
from ctf_workbench.services.outbox import dispatch_pending, pending_rows


def _engine():
    engine = create_engine_from_url(get_settings().database_url)
    return engine, session_factory(engine)


def test_outbox_marks_delivered_only_after_ack() -> None:
    engine, factory = _engine()
    events = EventService()
    actor_id = new_id()
    seen: list[str] = []
    with session_scope(factory) as session:
        session.add(Actor(id=actor_id, kind=ActorKind.HUMAN.value, display_name="outbox"))
        event = events.append(session, actor_id=actor_id, type="probe", payload={})
        event_id = event.id
        assert pending_rows(session)

        def fail_once(item: Event) -> None:
            raise RuntimeError("transport down")

        assert dispatch_pending(session, fail_once) == 0
        row = session.get(Outbox, pending_rows(session)[0].id)
        assert row is not None
        assert row.delivered_at is None
        assert row.attempts == 1

        dispatch_pending(session, lambda item: seen.append(item.id))
        remaining = pending_rows(session)
        assert remaining == []
        assert seen == [event_id]
    engine.dispose()


def test_duplicate_delivery_is_deduped_by_event_id() -> None:
    engine, factory = _engine()
    events = EventService()
    actor_id = new_id()
    seen: list[str] = []

    def record(item: Event) -> None:
        seen.append(item.id)

    with session_scope(factory) as session:
        session.add(Actor(id=actor_id, kind=ActorKind.HUMAN.value, display_name="dup"))
        event = events.append(session, actor_id=actor_id, type="probe", payload={})
        event_id = event.id
        dispatch_pending(session, record)
        # Crash-after-send: another worker retries the same payload.
        record(event)
        unique = list(dict.fromkeys(seen))
        assert unique == [event_id]
        assert seen.count(event_id) == 2
    engine.dispose()
