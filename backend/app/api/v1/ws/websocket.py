"""WebSocket Router for Real-Time Conversation Synchronization."""

from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections for admin dashboard live updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_message(self, message_data: dict):
        """Broadcast a message event to all connected dashboard clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message_data)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time live chat monitoring."""
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
