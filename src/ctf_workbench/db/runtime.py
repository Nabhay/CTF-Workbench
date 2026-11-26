from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ctf_workbench.config import Settings, get_settings
from ctf_workbench.db.bootstrap import ensure_local_admin
from ctf_workbench.db.engine import create_engine_from_settings, ping_database, session_factory, session_scope
from ctf_workbench.db.migrations import assert_schema_at_head
from ctf_workbench.domain.errors import SchemaMismatchError
from ctf_workbench.services.events import EventService


@dataclass
class Database:
    engine: Engine
    sessions: sessionmaker[Session]
    events: EventService


_database: Database | None = None


def init_database(settings: Settings | None = None, *, require_migrations: bool = True) -> Database:
    global _database
    resolved = settings or get_settings()
    engine = create_engine_from_settings(resolved)
    if require_migrations:
        assert_schema_at_head(engine)
    factory = session_factory(engine)
    events = EventService()
    with session_scope(factory) as session:
        ensure_local_admin(session, events)
    _database = Database(engine=engine, sessions=factory, events=events)
    return _database


def get_database() -> Database:
    if _database is None:
        raise RuntimeError("Database is not initialized. The API lifespan did not run.")
    return _database


def reset_database() -> None:
    global _database
    if _database is not None:
        _database.engine.dispose()
    _database = None


def database_status(engine: Engine) -> str:
    try:
        ping_database(engine)
    except Exception:
        return "unavailable"
    try:
        assert_schema_at_head(engine)
    except SchemaMismatchError:
        return "unmigrated"
    return "ok"
