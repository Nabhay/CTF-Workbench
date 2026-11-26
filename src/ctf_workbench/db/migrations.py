from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.engine import Engine

from ctf_workbench.domain.errors import SchemaMismatchError

ROOT = Path(__file__).resolve().parents[3]


def alembic_config(database_url: str) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def upgrade_to_head(database_url: str) -> None:
    command.upgrade(alembic_config(database_url), "head")


def current_and_head_revisions(
    engine: Engine, database_url: str | None = None
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    url = database_url or engine.url.render_as_string(hide_password=False)
    script = ScriptDirectory.from_config(alembic_config(url))
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        current = tuple(context.get_current_heads())
    heads = tuple(script.get_heads())
    return current, heads


def assert_schema_at_head(engine: Engine) -> None:
    current, heads = current_and_head_revisions(engine)
    if current != heads:
        raise SchemaMismatchError(
            "Database schema is not at Alembic head. "
            f"current={current or '(empty)'} head={heads}. "
            "Run: uv run alembic upgrade head"
        )
