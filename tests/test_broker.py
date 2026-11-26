from __future__ import annotations

import asyncio

from ctf_workbench.services.broker import OVERFLOW, StreamBroker


def test_slow_consumer_is_disconnected_with_resume_cursor() -> None:
    async def run() -> None:
        broker = StreamBroker(max_queue=3)
        sub = broker.subscribe("global")
        for seq in range(8):
            broker.publish({"stream_id": "global", "seq": seq, "id": str(seq)})
        assert sub.overflow is True
        assert sub.resume_seq is not None
        messages = []
        while not sub.queue.empty():
            messages.append(sub.queue.get_nowait())
        assert any(message.get("error") == OVERFLOW for message in messages)

    asyncio.run(run())
