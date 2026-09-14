"""Real-time Server-Sent Events (SSE) Broadcaster for AI Control Plane.

Streams live telemetry, active agent runs, evaluation progress, guardrail alerts,
and release state changes directly to connected developer dashboards.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, Set

logger = logging.getLogger(__name__)


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AIControlPlaneEventBroadcaster:
    """Asynchronous pub/sub broadcaster for SSE client listeners."""

    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue:
        """Register a new SSE stream subscriber queue."""
        q = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers.add(q)
        # Send initial connected heartbeat
        await q.put({
            "event": "CONNECTED",
            "timestamp": utc_iso(),
            "data": {"status": "ONLINE", "stream": "ai_control_plane_sse"}
        })
        return q

    async def unsubscribe(self, q: asyncio.Queue):
        """Remove an inactive or disconnected SSE subscriber queue."""
        async with self._lock:
            self._subscribers.discard(q)

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Publish an event to all active developer listeners."""
        payload = {
            "event": event_type,
            "timestamp": utc_iso(),
            "data": data,
        }
        async with self._lock:
            subs = list(self._subscribers)

        for q in subs:
            try:
                if not q.full():
                    q.put_nowait(payload)
            except Exception as e:
                logger.debug(f"Failed to deliver SSE event: {e}")

    async def event_generator(self, queue: asyncio.Queue) -> AsyncGenerator[str, None]:
        """Format queued dictionary events into RFC-8895 Server-Sent Events string protocol."""
        try:
            while True:
                # Wait for next event or send 15s keepalive heartbeat
                try:
                    event_dict = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"event: {event_dict.get('event', 'message')}\ndata: {json.dumps(event_dict)}\n\n"
                except asyncio.TimeoutError:
                    heartbeat = {
                        "event": "HEARTBEAT",
                        "timestamp": utc_iso(),
                        "data": {"ping": "keepalive"}
                    }
                    yield f"event: HEARTBEAT\ndata: {json.dumps(heartbeat)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            await self.unsubscribe(queue)


ai_event_broadcaster = AIControlPlaneEventBroadcaster()
