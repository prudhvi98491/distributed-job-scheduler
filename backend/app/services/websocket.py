"""WebSocket connection manager for real-time dashboard updates."""
import json
import asyncio
from typing import Set
from fastapi import WebSocket

# Global set of active WebSocket connections
_connections: Set[WebSocket] = set()


async def register(ws: WebSocket):
    """Register a new WebSocket connection."""
    await ws.accept()
    _connections.add(ws)


def unregister(ws: WebSocket):
    """Remove a WebSocket connection."""
    _connections.discard(ws)


async def broadcast(data: dict):
    """Broadcast a JSON message to all connected clients."""
    if not _connections:
        return
    message = json.dumps(data, default=str)
    dead = set()
    for ws in list(_connections):
        try:
            await ws.send_text(message)
        except Exception:
            dead.add(ws)
    for ws in dead:
        _connections.discard(ws)


def connection_count() -> int:
    return len(_connections)
