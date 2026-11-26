import { useEffect, useRef, useState } from "react";

import { wsUrl } from "@/shared/config";

type StreamEvent = {
  id: string;
  seq: number;
  type: string;
};

export function EventStream({ enabled }: { enabled: boolean }) {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [status, setStatus] = useState<"off" | "live" | "retrying">("off");
  const afterSeq = useRef(0);
  const seen = useRef(new Set<string>());

  useEffect(() => {
    if (!enabled) {
      setStatus("off");
      return;
    }
    let socket: WebSocket | null = null;
    let retry: number | undefined;
    let stopped = false;

    const connect = () => {
      if (stopped) {
        return;
      }
      const url = wsUrl(`/api/v1/ws/events?stream_id=global&after_seq=${afterSeq.current}`);
      socket = new WebSocket(url);
      socket.onopen = () => setStatus("live");
      socket.onmessage = (message) => {
        const payload = JSON.parse(message.data) as {
          id?: string;
          seq?: number;
          type?: string;
          error?: string;
          resume_seq?: number;
        };
        if (payload.error === "slow_consumer" && typeof payload.resume_seq === "number") {
          afterSeq.current = payload.resume_seq;
          return;
        }
        if (!payload.id || payload.seq === undefined || !payload.type) {
          return;
        }
        const next: StreamEvent = { id: payload.id, seq: payload.seq, type: payload.type };
        if (seen.current.has(next.id)) {
          return;
        }
        seen.current.add(next.id);
        afterSeq.current = next.seq;
        setEvents((current) => [...current, next].slice(-12));
      };
      socket.onclose = (event) => {
        if (stopped || event.code === 1008) {
          setStatus("off");
          return;
        }
        setStatus("retrying");
        retry = window.setTimeout(connect, 1500);
      };
    };

    connect();
    return () => {
      stopped = true;
      if (retry !== undefined) {
        window.clearTimeout(retry);
      }
      socket?.close();
    };
  }, [enabled]);

  return (
    <section className="mt-12 border-t border-edge pt-8">
      <div className="flex items-baseline justify-between gap-4">
        <h2 className="text-lg font-semibold">Event stream</h2>
        <p className="font-mono text-xs text-mute">{status}</p>
      </div>
      {events.length === 0 ? (
        <p className="mt-4 font-mono text-sm text-mute">Waiting for the first event on stream global.</p>
      ) : (
        <ol className="mt-4 grid gap-1 font-mono text-sm">
          {events.map((event) => (
            <li key={event.id}>
              <span className="text-mute">{event.seq}</span>
              <span className="ml-3">{event.type}</span>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}