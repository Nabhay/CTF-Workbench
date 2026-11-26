from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ctf_workbench.api.main import create_app
from ctf_workbench.config import reset_settings_cache
from ctf_workbench.db.blobs import blob_storage_key
from ctf_workbench.db.engine import session_scope
from ctf_workbench.db.models import Artifact, Blob, Challenge, Competition
from ctf_workbench.db.runtime import get_database
from ctf_workbench.domain.ids import LOCAL_ADMIN_ACTOR_ID, new_id
from ctf_workbench.domain.refs import ByteSelector, ResourceRef


def test_byte_selector_rejects_inverted_range() -> None:
    with pytest.raises(ValidationError):
        ByteSelector(start=10, end_exclusive=10)


def _seed_artifact(*, size: int = 32, digest: str | None = None) -> tuple[str, str, str]:
    digest = digest or ("ab" * 32)
    db = get_database()
    competition_id = new_id()
    challenge_id = new_id()
    artifact_id = new_id()
    with session_scope(db.sessions) as session:
        session.add(Competition(id=competition_id, title="ref-event"))
        session.add(Challenge(id=challenge_id, competition_id=competition_id, title="ref-chal"))
        session.flush()
        event = db.events.append(
            session,
            actor_id=LOCAL_ADMIN_ACTOR_ID,
            type="artifact.imported",
            payload={"artifact_id": artifact_id},
            challenge_id=challenge_id,
        )
        session.add(Blob(sha256=digest, size_bytes=size, storage_key=blob_storage_key(digest)))
        session.flush()
        session.add(
            Artifact(
                id=artifact_id,
                challenge_id=challenge_id,
                blob_sha256=digest,
                display_name="sample.bin",
                origin_event_id=event.id,
            )
        )
    return challenge_id, artifact_id, digest


def test_resolve_ref_accepts_in_range_bytes() -> None:
    reset_settings_cache()
    app = create_app()
    with TestClient(app) as client:
        challenge_id, artifact_id, digest = _seed_artifact()
        response = client.post(
            "/api/v1/refs/resolve",
            json={
                "kind": "artifact",
                "id": artifact_id,
                "challenge_id": challenge_id,
                "version": digest,
                "selector": {"start": 0, "end_exclusive": 8},
            },
        )
        assert response.status_code == 200
        assert response.json()["version"] == digest


def test_stale_version_returns_structured_conflict() -> None:
    reset_settings_cache()
    app = create_app()
    with TestClient(app) as client:
        challenge_id, artifact_id, digest = _seed_artifact()
        response = client.post(
            "/api/v1/refs/resolve",
            json={
                "kind": "artifact",
                "id": artifact_id,
                "challenge_id": challenge_id,
                "version": "00" * 32,
                "selector": {"start": 0, "end_exclusive": 4},
            },
        )
        assert response.status_code == 409
        body = response.json()
        assert body["error"]["code"] == "stale_reference"
        assert body["error"]["details"]["current_version"] == digest


def test_missing_artifact_is_not_found() -> None:
    reset_settings_cache()
    app = create_app()
    with TestClient(app) as client:
        challenge_id, _, digest = _seed_artifact()
        response = client.post(
            "/api/v1/refs/resolve",
            json={
                "kind": "artifact",
                "id": new_id(),
                "challenge_id": challenge_id,
                "version": digest,
            },
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "not_found"


def test_resource_ref_round_trip_model() -> None:
    ref = ResourceRef(
        kind="artifact",
        id=new_id(),
        challenge_id=new_id(),
        version="ab" * 32,
        selector=ByteSelector(start=2, end_exclusive=10),
    )
    dumped = ref.model_dump()
    assert dumped["selector"]["start"] == 2
