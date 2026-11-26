from __future__ import annotations

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from ctf_workbench.config import get_settings
from ctf_workbench.db.blobs import blob_storage_key
from ctf_workbench.db.engine import create_engine_from_url, session_factory, session_scope
from ctf_workbench.db.migrations import current_and_head_revisions, upgrade_to_head
from ctf_workbench.db.models import Actor, Challenge, Competition, Event, Outbox
from ctf_workbench.db.runtime import init_database, reset_database
from ctf_workbench.domain.enums import ActorKind
from ctf_workbench.domain.errors import ConflictError
from ctf_workbench.domain.ids import LOCAL_ADMIN_ACTOR_ID, new_id
from ctf_workbench.domain.pagination import clamp_page_size, decode_cursor, encode_cursor
from ctf_workbench.services.events import EventService
from ctf_workbench.services.revisions import cas_update


def test_empty_database_upgrades_to_head() -> None:
    engine = create_engine_from_url(get_settings().database_url)
    current, heads = current_and_head_revisions(engine)
    assert current == heads
    assert heads != ()
    engine.dispose()


def test_sqlite_enables_wal_and_foreign_keys() -> None:
    engine = create_engine_from_url(get_settings().database_url)
    with engine.connect() as connection:
        journal = connection.execute(text("PRAGMA journal_mode")).scalar()
        foreign_keys = connection.execute(text("PRAGMA foreign_keys")).scalar()
        timeout = connection.execute(text("PRAGMA busy_timeout")).scalar()
    engine.dispose()
    assert str(journal).lower() == "wal"
    assert int(foreign_keys) == 1
    assert int(timeout) == 5000


def test_fixtures_survive_close_and_reopen() -> None:
    url = get_settings().database_url
    engine = create_engine_from_url(url)
    factory = session_factory(engine)
    competition_id = new_id()
    with session_scope(factory) as session:
        session.add(
            Competition(
                id=competition_id,
                title="Weekend CTF",
                rules_text="authorized event",
                assistance_policy_json={"agents": False},
            )
        )
    engine.dispose()

    engine = create_engine_from_url(url)
    factory = session_factory(engine)
    with session_scope(factory) as session:
        loaded = session.get(Competition, competition_id)
        assert loaded is not None
        assert loaded.title == "Weekend CTF"
        assert loaded.revision == 1
    engine.dispose()


def test_invalid_foreign_keys_fail() -> None:
    engine = create_engine_from_url(get_settings().database_url)
    factory = session_factory(engine)
    with pytest.raises(IntegrityError):
        with session_scope(factory) as session:
            session.add(
                Challenge(
                    id=new_id(),
                    competition_id=new_id(),
                    title="orphan",
                )
            )
    engine.dispose()


def test_stale_revision_update_conflicts() -> None:
    engine = create_engine_from_url(get_settings().database_url)
    factory = session_factory(engine)
    competition_id = new_id()
    with session_scope(factory) as session:
        session.add(Competition(id=competition_id, title="original"))

    first = factory()
    second = factory()
    try:
        cas_update(
            first,
            Competition,
            entity_id=competition_id,
            expected_revision=1,
            values={"title": "first writer"},
        )
        first.commit()
        with pytest.raises(ConflictError) as exc:
            cas_update(
                second,
                Competition,
                entity_id=competition_id,
                expected_revision=1,
                values={"title": "second writer"},
            )
            second.commit()
        assert exc.value.current_revision == 2
    finally:
        first.close()
        second.close()
        engine.dispose()


def test_state_and_event_roll_back_together() -> None:
    engine = create_engine_from_url(get_settings().database_url)
    factory = session_factory(engine)
    events = EventService()
    actor_id = new_id()
    competition_id = new_id()
    with session_scope(factory) as session:
        session.add(Actor(id=actor_id, kind=ActorKind.HUMAN.value, display_name="tester"))

    with pytest.raises(RuntimeError, match="boom"):
        with session_scope(factory) as session:
            session.add(Competition(id=competition_id, title="will roll back"))
            events.append(
                session,
                actor_id=actor_id,
                type="competition.created",
                payload={"competition_id": competition_id},
            )
            raise RuntimeError("boom")

    with session_scope(factory) as session:
        assert session.get(Competition, competition_id) is None
        leftover_events = (
            session.execute(select(Event).where(Event.type == "competition.created")).scalars().all()
        )
        leftover_outbox = session.execute(select(Outbox)).scalars().all()
        assert leftover_events == []
        assert leftover_outbox == []

    engine.dispose()


def test_event_sequences_are_monotonic() -> None:
    engine = create_engine_from_url(get_settings().database_url)
    factory = session_factory(engine)
    events = EventService()
    actor_id = new_id()
    with session_scope(factory) as session:
        session.add(Actor(id=actor_id, kind=ActorKind.SYSTEM.value, display_name="seq"))
        first = events.append(session, actor_id=actor_id, type="ping", payload={"n": 1})
        second = events.append(session, actor_id=actor_id, type="ping", payload={"n": 2})
        assert first.seq == 1
        assert second.seq == 2
        assert first.stream_id == second.stream_id
    engine.dispose()


def test_bootstrap_creates_local_admin() -> None:
    reset_database()
    db = init_database(get_settings())
    with session_scope(db.sessions) as session:
        admin = session.get(Actor, LOCAL_ADMIN_ACTOR_ID)
        assert admin is not None
        assert admin.kind == ActorKind.HUMAN.value
        assert admin.display_name == "local-admin"
    reset_database()


def test_blob_storage_key_is_not_a_user_path() -> None:
    digest = "a" * 64
    key = blob_storage_key(digest)
    assert key == f"blobs/aa/{digest}"
    assert "\\" not in key
    assert not key.startswith("/")


def test_page_size_is_bounded() -> None:
    assert clamp_page_size(None) == 50
    assert clamp_page_size(200) == 200
    assert clamp_page_size(500) == 200
    with pytest.raises(ValueError):
        clamp_page_size(0)


def test_cursor_round_trip() -> None:
    from datetime import UTC, datetime

    created = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
    cursor = encode_cursor(created_at=created, id="abc")
    decoded_at, decoded_id = decode_cursor(cursor)
    assert decoded_id == "abc"
    assert decoded_at == created


def test_upgrade_is_idempotent() -> None:
    url = get_settings().database_url
    upgrade_to_head(url)
    upgrade_to_head(url)
    engine = create_engine_from_url(url)
    current, heads = current_and_head_revisions(engine)
    engine.dispose()
    assert current == heads
