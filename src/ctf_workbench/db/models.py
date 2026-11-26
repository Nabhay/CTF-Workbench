from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ctf_workbench.db.base import Base
from ctf_workbench.domain.enums import ActorKind, ChallengeStatus, ItemKind, ItemStatus
from ctf_workbench.domain.ids import new_id


def utcnow() -> datetime:
    return datetime.now(UTC)


class Competition(Base):
    __tablename__ = "competitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    rules_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    assistance_policy_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    flag_pattern: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class Actor(Base):
    __tablename__ = "actors"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('human', 'tool', 'agent', 'system')",
            name="actor_kind",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    kind: Mapped[str] = mapped_column(String(16), nullable=False, default=ActorKind.HUMAN.value)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class Challenge(Base):
    __tablename__ = "challenges"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'in_progress', 'solved', 'archived')",
            name="challenge_status",
        ),
        CheckConstraint("points IS NULL OR points >= 0", name="challenge_points_nonnegative"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    competition_id: Mapped[str] = mapped_column(
        ForeignKey("competitions.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="manual")
    external_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    hints_json: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    scope_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=ChallengeStatus.OPEN.value)
    owner_id: Mapped[str | None] = mapped_column(ForeignKey("actors.id"), nullable=True)
    parent_meta_id: Mapped[str | None] = mapped_column(ForeignKey("challenges.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    competition: Mapped[Competition] = relationship()


class Blob(Base):
    __tablename__ = "blobs"

    sha256: Mapped[str] = mapped_column(String(64), primary_key=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class EventStream(Base):
    __tablename__ = "event_streams"

    stream_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    next_seq: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("stream_id", "seq", name="uq_events_stream_seq"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    stream_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"), nullable=False)
    challenge_id: Mapped[str | None] = mapped_column(ForeignKey("challenges.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(128), nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    challenge_id: Mapped[str] = mapped_column(ForeignKey("challenges.id"), nullable=False, index=True)
    blob_sha256: Mapped[str] = mapped_column(ForeignKey("blobs.sha256"), nullable=False)
    display_name: Mapped[str] = mapped_column(String(512), nullable=False)
    media_type: Mapped[str] = mapped_column(String(128), nullable=False, default="application/octet-stream")
    kind: Mapped[str] = mapped_column(String(64), nullable=False, default="file")
    origin_event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class ArtifactParent(Base):
    __tablename__ = "artifact_parents"

    child_artifact_id: Mapped[str] = mapped_column(
        ForeignKey("artifacts.id"), primary_key=True
    )
    parent_artifact_id: Mapped[str] = mapped_column(
        ForeignKey("artifacts.id"), primary_key=True
    )


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        CheckConstraint("kind IN ('lead', 'fact', 'dead_end')", name="item_kind"),
        CheckConstraint(
            "status IN ('hypothesis', 'verified', 'confirmed', 'dead_end')",
            name="item_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    challenge_id: Mapped[str] = mapped_column(ForeignKey("challenges.id"), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default=ItemKind.LEAD.value)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=ItemStatus.HYPOTHESIS.value)
    author_id: Mapped[str] = mapped_column(ForeignKey("actors.id"), nullable=False)
    pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by_event: Mapped[str] = mapped_column(ForeignKey("events.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    challenge_id: Mapped[str] = mapped_column(ForeignKey("challenges.id"), nullable=False, index=True)
    item_id: Mapped[str | None] = mapped_column(ForeignKey("items.id"), nullable=True)
    artifact_id: Mapped[str | None] = mapped_column(ForeignKey("artifacts.id"), nullable=True)
    tool_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    selector_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    predicate_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    rerunnable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class Link(Base):
    __tablename__ = "links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    competition_id: Mapped[str] = mapped_column(ForeignKey("competitions.id"), nullable=False, index=True)
    from_type: Mapped[str] = mapped_column(String(32), nullable=False)
    from_id: Mapped[str] = mapped_column(String(36), nullable=False)
    to_type: Mapped[str] = mapped_column(String(32), nullable=False)
    to_id: Mapped[str] = mapped_column(String(36), nullable=False)
    relation: Mapped[str] = mapped_column(String(32), nullable=False)
    created_by_event: Mapped[str] = mapped_column(ForeignKey("events.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    challenge_id: Mapped[str] = mapped_column(ForeignKey("challenges.id"), nullable=False, index=True)
    content_json: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class Outbox(Base):
    __tablename__ = "outbox"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), nullable=False, index=True)
    destination: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
