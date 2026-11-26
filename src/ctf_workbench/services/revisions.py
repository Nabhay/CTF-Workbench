from __future__ import annotations

from typing import Any

from sqlalchemy import update
from sqlalchemy.orm import Session

from ctf_workbench.domain.errors import ConflictError


def cas_update(
    session: Session,
    model: type[Any],
    *,
    entity_id: str,
    expected_revision: int,
    values: dict[str, Any],
) -> None:
    payload = {**values, "revision": expected_revision + 1}
    result = session.execute(
        update(model)
        .where(model.id == entity_id, model.revision == expected_revision)
        .values(**payload)
    )
    if result.rowcount != 1:
        current = session.get(model, entity_id)
        current_revision = getattr(current, "revision", None) if current is not None else None
        raise ConflictError(
            "revision conflict: the record changed since this client last read it",
            current_revision=current_revision,
        )
