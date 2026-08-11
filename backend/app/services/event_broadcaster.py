"""Event Broadcaster Service — Server-Sent Events (SSE) Broadcast Engine."""

import asyncio
import json
from typing import Dict, List, AsyncGenerator


class EventBroadcaster:
    """Manages active SSE client subscriber queues and broadcasts real-time events."""

    def __init__(self):
        self._subscribers: List[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        """Register a new SSE client listener queue."""
        queue: asyncio.Queue = asyncio.Queue()
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
            except Exception:
                pass


# Global singleton instance
broadcaster = EventBroadcaster()
