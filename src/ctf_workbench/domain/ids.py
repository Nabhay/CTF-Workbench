from __future__ import annotations

import uuid

LOCAL_ADMIN_ACTOR_ID = "00000000-0000-4000-8000-000000000001"
GLOBAL_STREAM_ID = "global"


def new_id() -> str:
    return str(uuid.uuid4())
