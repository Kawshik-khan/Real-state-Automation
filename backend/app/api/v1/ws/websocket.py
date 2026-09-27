"""WebSocket Router for Real-Time Conversation Synchronization."""

import asyncio
from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.dependencies import authenticate_websocket
from app.models.user import UserRole

router = APIRouter()

_WS_ROLES = [UserRole.ADMIN, UserRole.MANAGER, UserRole.AGENT, UserRole.DEVELOPER]
_SEND_TIMEOUT_SECONDS = 5.0


class ConnectionManager:
    """Manages active WebSocket connections for admin dashboard live updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        # Caller must have authenticated the socket before this point.
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_message(self, message_data: dict):
        """Broadcast a message event to all connected dashboard clients."""
        disconnected = []
        for connection in list(self.active_connections):
            try:
                # A stalled client must not block delivery to everyone else.
                await asyncio.wait_for(connection.send_json(message_data), timeout=_SEND_TIMEOUT_SECONDS)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time live chat monitoring (requires ``?ticket=``)."""
    if not await authenticate_websocket(websocket, _WS_ROLES):
        return
    await manager.connect(websocket)
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "event": "connected",
            "message": "Real-time conversation stream active"
        })

        while True:
            # Keep connection open and accept client pings/messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
