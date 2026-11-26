from __future__ import annotations

from typing import Self

from pydantic import BaseModel, Field, model_validator

from ctf_workbench.domain.errors import StaleReferenceError


class ByteSelector(BaseModel):
    start: int = Field(ge=0)
    end_exclusive: int = Field(ge=0)

    @model_validator(mode="after")
    def _ordered(self) -> Self:
        if self.end_exclusive <= self.start:
            raise ValueError("byte selector requires end_exclusive > start")
        return self


class TextSelector(BaseModel):
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    column_start: int = Field(ge=0)
    column_end: int = Field(ge=0)

    @model_validator(mode="after")
    def _ordered(self) -> Self:
        if self.line_end < self.line_start:
            raise ValueError("text selector requires line_end >= line_start")
        if self.line_start == self.line_end and self.column_end < self.column_start:
            raise ValueError("text selector requires column_end >= column_start on the same line")
        return self


class PacketSelector(BaseModel):
    packet_number: int = Field(ge=1)
    stream_id: str = Field(min_length=1)


class ImageSelector(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class FunctionSelector(BaseModel):
    address: str = Field(min_length=1)
    analysis_revision: int = Field(ge=1)


class ResourceRef(BaseModel):
    kind: str = Field(min_length=1, max_length=64)
    id: str = Field(min_length=1, max_length=64)
    challenge_id: str = Field(min_length=1, max_length=36)
    version: str = Field(min_length=1, max_length=64)
    selector: ByteSelector | TextSelector | PacketSelector | ImageSelector | FunctionSelector | None = None


def assert_byte_range_fits(selector: ByteSelector, *, size_bytes: int) -> None:
    if selector.end_exclusive > size_bytes:
        raise ValueError(
            f"byte selector [{selector.start},{selector.end_exclusive}) is outside version size {size_bytes}"
        )


def assert_immutable_version(*, expected: str, actual: str) -> None:
    if expected != actual:
        raise StaleReferenceError(
            "resource version does not match the immutable object; "
            "snapshot the workspace before selecting mutable bytes",
            current_version=actual,
        )
