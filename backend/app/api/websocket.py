"""
WebSocket Manager & Router for Real-time Operations Dashboard.

Clients connect via `ws://localhost:8000/api/ws/status/{application_id}` to receive
real-time status updates as events flow through the Saga Orchestrator.
"""
from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Manages active WebSocket connections per application ID."""

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, application_id: str) -> None:
        await websocket.accept()
        self.active_connections[application_id].append(websocket)
        logger.info("WebSocket client connected for application %s", application_id)

    def disconnect(self, websocket: WebSocket, application_id: str) -> None:
        if websocket in self.active_connections[application_id]:
            self.active_connections[application_id].remove(websocket)
            logger.info("WebSocket client disconnected for application %s", application_id)

    async def broadcast_status(self, application_id: str, data: dict) -> None:
        connections = self.active_connections.get(application_id, [])
        if not connections:
            return
        message = json.dumps(data)
        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception as exc:
                logger.error("Failed to send WS message: %s", exc)


ws_manager = ConnectionManager()


@router.websocket("/ws/status/{application_id}")
async def websocket_application_status(websocket: WebSocket, application_id: str):
    await ws_manager.connect(websocket, application_id)
    try:
        while True:
            # Keep connection open & handle ping/pong
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, application_id)
