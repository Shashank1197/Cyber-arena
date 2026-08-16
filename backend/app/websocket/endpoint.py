#!/usr/bin/env python3
"""FastAPI WebSocket endpoint that funnels messages into the GameServer."""
from __future__ import annotations

import json
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..state import game_server

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    conn_id = str(uuid4())
    await game_server.handle_connect(conn_id, ws)
    try:
        while True:
            raw = await ws.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = {"type": "__invalid__"}
            if not isinstance(data, dict):
                data = {"type": "__invalid__"}
            await game_server.handle_message(conn_id, data)
    except WebSocketDisconnect:
        await game_server.handle_disconnect(conn_id)
    except Exception:
        # Unexpected socket-level error: clean up so the match can continue.
        await game_server.handle_disconnect(conn_id)
