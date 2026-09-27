"""Event Broadcaster Service — Server-Sent Events (SSE) Broadcast Engine."""

import asyncio
from typing import Dict, List


class EventBroadcaster:
    """Manages active SSE client subscriber queues and broadcasts real-time events."""

    def __init__(self):
        self._subscribers: List[asyncio.Queue] = []

    def subscribe(self, maxsize: int = 256) -> asyncio.Queue:
        """Register a new SSE client listener queue with bounded capacity."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        """Remove an SSE client listener queue."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    async def broadcast(self, event_type: str, data: Dict) -> None:
        """Broadcast a structured JSON payload to all connected SSE clients."""
        payload = {
            "event": event_type,
            "data": data,
        }
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                # Evict oldest message to prevent unbounded memory growth on slow consumers
                try:
                    queue.get_nowait()
                    queue.put_nowait(payload)
                except Exception:
                    pass
            except Exception:
                pass


# Global singleton instance
broadcaster = EventBroadcaster()
