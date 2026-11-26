from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ctf_workbench.db.engine import session_scope
from ctf_workbench.db.runtime import get_database
from ctf_workbench.domain.refs import ResourceRef
from ctf_workbench.services.refs import resolve_ref

router = APIRouter()


class ResolvedRef(BaseModel):
    kind: str
    id: str
    challenge_id: str
    version: str
    valid: bool = True


@router.post("/api/v1/refs/resolve", response_model=ResolvedRef)
def resolve_resource_ref(ref: ResourceRef) -> ResolvedRef:
    db = get_database()
    with session_scope(db.sessions) as session:
        artifact = resolve_ref(session, ref)
        return ResolvedRef(
            kind=ref.kind,
            id=artifact.id,
            challenge_id=artifact.challenge_id,
            version=artifact.blob_sha256,
        )
