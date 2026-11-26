from __future__ import annotations

from sqlalchemy.orm import Session

from ctf_workbench.db.models import Artifact, Blob, Challenge
from ctf_workbench.domain.errors import NotFoundError
from ctf_workbench.domain.refs import ByteSelector, ResourceRef, assert_byte_range_fits, assert_immutable_version


def resolve_ref(session: Session, ref: ResourceRef) -> Artifact:
    challenge = session.get(Challenge, ref.challenge_id)
    if challenge is None:
        raise NotFoundError("challenge is absent or inaccessible")
    artifact = session.get(Artifact, ref.id)
    if artifact is None or artifact.challenge_id != ref.challenge_id:
        raise NotFoundError("artifact is absent or inaccessible")
    blob = session.get(Blob, artifact.blob_sha256)
    if blob is None:
        raise NotFoundError("blob for this artifact is absent")
    assert_immutable_version(expected=ref.version, actual=blob.sha256)
    if isinstance(ref.selector, ByteSelector):
        assert_byte_range_fits(ref.selector, size_bytes=blob.size_bytes)
    return artifact
