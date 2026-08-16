"""Real-time Log Streamer & Telemetry Ring Buffer Service."""

import asyncio
import logging
import time
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RealtimeLogEntry(BaseModel):
    """Structured real-time log event."""
    id: str = Field(default_factory=lambda: f"log_{int(time.time() * 1000)}_{hash(time.time()) % 10000}")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().strftime("%H:%M:%S.%f")[:-3])
    iso_time: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = "INFO"  # DEBUG, INFO, WARN, ERROR, CRITICAL
    module: str = "System"
    message: str
    path: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    latency_ms: Optional[float] = None
    client_ip: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class LogStreamerService:
    """Manages circular in-memory buffer of real-time application logs and SSE event broadcasting."""

    def __init__(self, max_buffer_size: int = 1000):
        self._buffer: deque[RealtimeLogEntry] = deque(maxlen=max_buffer_size)
        self._subscribers: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()
        
        # Seed initial system startup events
        self.record_log(
            level="INFO",
            module="LogStreamer",
            message="Live real-time telemetry logging engine initialized and active"
        )

    def record_log(
        self,
        level: str,
        module: str,
        message: str,
        path: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        latency_ms: Optional[float] = None,
        client_ip: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> RealtimeLogEntry:
        """Record a live log entry into the circular buffer and broadcast to active SSE subscribers."""
        entry = RealtimeLogEntry(
            level=level.upper(),
            module=module,
            message=message,
            path=path,
            method=method,
            status_code=status_code,
            latency_ms=latency_ms,
            client_ip=client_ip,
            details=details
        )
        self._buffer.appendleft(entry)
        
        # Broadcast asynchronously to connected SSE clients
        if self._subscribers:
            for q in list(self._subscribers):
                try:
                    q.put_nowait(entry.model_dump())
                except Exception:
                    pass
                    
        return entry

    def get_logs(
        self,
        limit: int = 100,
        level: Optional[str] = None,
        module: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve recent logs from the circular buffer with optional filtering."""
        results = []
        for entry in self._buffer:
            if level and level.upper() != "ALL" and entry.level != level.upper():
                continue
            if module and module.lower() not in entry.module.lower():
                continue
            if search:
                s = search.lower()
                if s not in entry.message.lower() and s not in entry.module.lower() and (not entry.path or s not in entry.path.lower()):
                    continue
            results.append(entry.model_dump())
            if len(results) >= limit:
                break
        return results

    def clear_logs(self) -> None:
        """Clear the in-memory log buffer."""
        self._buffer.clear()
        self.record_log(
            level="INFO",
            module="LogStreamer",
            message="Developer cleared live log buffer"
        )

    def subscribe(self) -> asyncio.Queue:
        """Register a new SSE client subscriber queue."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        """Unregister an SSE client subscriber queue."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)


# Global singleton instance
log_streamer = LogStreamerService()


class InterceptLoggingHandler(logging.Handler):
    """Custom standard logging handler that routes python logger outputs to the live log_streamer."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            level = record.levelname
            module = record.name.split(".")[-1]
            if module in ("uvicorn", "fastapi", "root"):
                module = "FastAPI"
            log_streamer.record_log(
                level=level,
                module=module,
                message=msg
            )
        except Exception:
            pass


# Configure intercept handler on root and app loggers
def setup_live_logging():
    handler = InterceptLoggingHandler()
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    
    app_logger = logging.getLogger("app")
    app_logger.addHandler(handler)
    app_logger.setLevel(logging.INFO)
