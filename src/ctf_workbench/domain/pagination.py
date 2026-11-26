from __future__ import annotations

import json
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime
from typing import Any

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


class CursorError(ValueError):
    """The supplied pagination cursor is not a valid opaque cursor."""


def clamp_page_size(limit: int | None) -> int:
    if limit is None:
        return DEFAULT_PAGE_SIZE
    if limit < 1:
        raise ValueError("page size must be at least 1")
    return min(limit, MAX_PAGE_SIZE)


def encode_cursor(*, created_at: datetime, id: str) -> str:
    payload = {"created_at": created_at.isoformat(), "id": id}
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, str]:
    padding = "=" * (-len(cursor) % 4)
    try:
        payload: Any = json.loads(urlsafe_b64decode(cursor + padding).decode("utf-8"))
        created_at = datetime.fromisoformat(payload["created_at"])
        id_ = str(payload["id"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CursorError("pagination cursor is not valid") from exc
    return created_at, id_
