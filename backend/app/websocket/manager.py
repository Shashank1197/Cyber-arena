#!/usr/bin/env python3
"""Tracks live WebSocket connections so the game server can push messages.

All access happens on a single asyncio event loop, so a plain dict keyed by
connection id is sufficient (no threading).
"""
from __future__ import annotations

import json
from typing import Optional

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._active: dict[str, WebSocket] = {}

    async def connect(self, connection_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._active[connection_id] = ws

    def disconnect(self, connection_id: str) -> None:
        self._active.pop(connection_id, None)

    def is_connected(self, connection_id: str) -> bool:
        return connection_id in self._active

    async def send(self, connection_id: str, payload: dict) -> None:
        ws = self._active.get(connection_id)
        if ws is None:
            return
        try:
            await ws.send_text(json.dumps(payload))
        except Exception:
            self._active.pop(connection_id, None)

    async def send_raw(self, connection_id: str, text: str) -> None:
        ws = self._active.get(connection_id)
        if ws is None:
            return
        try:
            await ws.send_text(text)
        except Exception:
            self._active.pop(connection_id, None)

    async def send_many(self, connection_ids: list[str], payload: dict) -> None:
        text = json.dumps(payload)
        for cid in connection_ids:
            await self.send_raw(cid, text)

    def connected_ids(self) -> list[str]:
        return list(self._active.keys())
