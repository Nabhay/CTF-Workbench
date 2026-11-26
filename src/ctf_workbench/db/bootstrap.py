from __future__ import annotations

from sqlalchemy.orm import Session

from ctf_workbench.db.models import Actor
from ctf_workbench.domain.enums import ActorKind
from ctf_workbench.domain.ids import LOCAL_ADMIN_ACTOR_ID
from ctf_workbench.services.events import EventService


def ensure_local_admin(session: Session, events: EventService) -> Actor:
    existing = session.get(Actor, LOCAL_ADMIN_ACTOR_ID)
    if existing is not None:
        return existing
    actor = Actor(
        id=LOCAL_ADMIN_ACTOR_ID,
        kind=ActorKind.HUMAN.value,
        display_name="local-admin",
    )
    session.add(actor)
    session.flush()
    events.append(
        session,
        actor_id=actor.id,
        type="actor.bootstrapped",
        payload={"actor_id": actor.id, "kind": actor.kind},
    )
    return actor
