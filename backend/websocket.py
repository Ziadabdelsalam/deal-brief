from fastapi import WebSocket
from typing import Dict, Set
import json

from models import DealStatus, WebSocketMessage


class WebSocketManager:
    """Manages WebSocket connections for real-time deal status updates."""

    def __init__(self):
        # Map of deal_id -> set of connected websockets
        self.connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, deal_id: str, websocket: WebSocket):
        """Accept connection and subscribe to deal updates."""
        await websocket.accept()
        if deal_id not in self.connections:
            self.connections[deal_id] = set()
        self.connections[deal_id].add(websocket)

    def disconnect(self, deal_id: str, websocket: WebSocket):
        """Remove connection from deal subscriptions."""
        if deal_id in self.connections:
            self.connections[deal_id].discard(websocket)
            if not self.connections[deal_id]:
                del self.connections[deal_id]

    async def broadcast_status(
        self, deal_id: str, status: DealStatus, error: str = None
    ):
        """Broadcast status update to all subscribers of a deal."""
        if deal_id not in self.connections:
            return

        message = WebSocketMessage(
            type="status_update",
            deal_id=deal_id,
            status=status,
            error=error,
        )

        dead_connections = set()
        for websocket in self.connections[deal_id]:
            try:
                await websocket.send_text(message.model_dump_json())
            except Exception:
                dead_connections.add(websocket)

        # Clean up dead connections
        for ws in dead_connections:
            self.connections[deal_id].discard(ws)


# Global instance
ws_manager = WebSocketManager()
