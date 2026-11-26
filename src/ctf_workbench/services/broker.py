from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

OVERFLOW = "slow_consumer"


@dataclass
class Subscription:
    stream_id: str
    queue: asyncio.Queue[dict[str, Any]]
    overflow: bool = False
    resume_seq: int | None = None


@dataclass
class StreamBroker:
    max_queue: int = 32
    _subs: dict[str, list[Subscription]] = field(default_factory=dict)

    def subscribe(self, stream_id: str) -> Subscription:
        sub = Subscription(stream_id=stream_id, queue=asyncio.Queue(maxsize=self.max_queue))
        self._subs.setdefault(stream_id, []).append(sub)
        return sub

    def unsubscribe(self, sub: Subscription) -> None:
        listeners = self._subs.get(sub.stream_id)
        if not listeners:
            return
        if sub in listeners:
            listeners.remove(sub)
        if not listeners:
            self._subs.pop(sub.stream_id, None)

    def publish(self, payload: dict[str, Any]) -> None:
        stream_id = str(payload["stream_id"])
        seq = int(payload["seq"])
        for sub in list(self._subs.get(stream_id, [])):
            if sub.overflow:
                continue
            if sub.queue.qsize() >= sub.queue.maxsize - 1:
                sub.overflow = True
                sub.resume_seq = seq
                try:
                    sub.queue.put_nowait({"error": OVERFLOW, "resume_seq": seq, "stream_id": stream_id})
                except asyncio.QueueFull:
                    pass
                continue
            try:
                sub.queue.put_nowait(payload)
            except asyncio.QueueFull:
                sub.overflow = True
                sub.resume_seq = seq
