"""WebSocket package."""
from app.api.v1.ws.websocket import manager as ws_manager
from app.api.v1.ws.websocket import router as ws_router

__all__ = ["ws_router", "ws_manager"]
