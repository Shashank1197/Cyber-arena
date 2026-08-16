#!/usr/bin/env python3
"""GameServer: wires WebSocket connections to rooms and drives the simulation.

Responsibilities:
  - accept/handle/disconnect connections
  - create/join/leave rooms
  - validate every client message before it touches the engine
  - run a countdown, then a fixed-rate tick loop that advances the engine
  - broadcast events + compact snapshots to the room
  - persist results and clean up empty rooms
"""
from __future__ import annotations

import asyncio
import logging
import time

from fastapi import WebSocket

from ..config.settings import get_settings
from ..rooms.room import Room, RoomError, RoomManager
from ..services.persistence import persistence
from ..utils.names import sanitize_name
from ..websocket.manager import ConnectionManager
from . import constants as C

log = logging.getLogger(__name__)
TICK_DELTA = 1.0 / C.TICK_RATE


class GameServer:
    def __init__(
        self,
        connections: ConnectionManager | None = None,
        rooms: RoomManager | None = None,
    ) -> None:
        self.connections = connections or ConnectionManager()
        self.rooms = rooms or RoomManager()
        self.settings = get_settings()
        self._bindings: dict[str, dict] = {}  # conn_id -> {player_id, room_code}
        self._match_tasks: dict[str, asyncio.Task] = {}  # room_code -> task

    # ---------------------------------------------------------- connection
    async def handle_connect(self, conn_id: str, ws: WebSocket) -> None:
        await self.connections.connect(conn_id, ws)
        await self.connections.send(
            conn_id,
            {"type": "welcome", "client_id": conn_id, "server_time": time.time()},
        )

    async def handle_disconnect(self, conn_id: str) -> None:
        binding = self._bindings.pop(conn_id, None)
        self.connections.disconnect(conn_id)
        if not binding:
            return
        player_id = binding["player_id"]
        room_code = binding["room_code"]
        room = self.rooms.get(room_code)
        if room is None:
            return
        room.clear_connection(conn_id)
        # Remove the player from live gameplay immediately (no frozen ghosts).
        if room.engine:
            room.engine.remove_player(player_id)
        await self._broadcast_room(room)
        # Allow a reconnect window, then purge the empty slot / room.
        asyncio.get_running_loop().create_task(
            self._cleanup_after_disconnect(room, player_id, conn_id)
        )

    async def _cleanup_after_disconnect(
        self, room: Room, player_id: str, conn_id: str
    ) -> None:
        await asyncio.sleep(C.RECONNECT_WINDOW_SECONDS)
        # A reconnect would have re-bound this connection.
        if self.connections.is_connected(conn_id):
            return
        current = room.get_player(player_id)
        if current and not current["connected"]:
            room.leave(player_id)
        if room.count_connected() == 0:
            self.rooms.remove(room.code)
            self._match_tasks.pop(room.code, None)
        else:
            await self._broadcast_room(room)

    # ---------------------------------------------------------- messaging
    async def handle_message(self, conn_id: str, msg: dict) -> None:
        mtype = msg.get("type")
        handler = getattr(self, f"_on_{mtype}", None) if mtype else None
        if handler is None:
            await self.connections.send(
                conn_id, {"type": "error", "code": "bad_request", "message": "Unknown message type."}
            )
            return
        try:
            await handler(conn_id, msg)
        except RoomError as exc:
            await self.connections.send(
                conn_id, {"type": "error", "code": exc.code, "message": exc.message}
            )
        except Exception as exc:  # noqa: BLE001 - report, never crash the loop
            log.exception("Error handling %s", mtype)
            await self.connections.send(
                conn_id, {"type": "error", "code": "internal", "message": "Server error."}
            )

    # ---- room lifecycle handlers
    async def _on_create_room(self, conn_id: str, msg: dict) -> None:
        name = sanitize_name(msg.get("name"))
        player_id = self._ensure_player_id(conn_id, msg)
        room = self.rooms.create(player_id, name)
        self._bind(conn_id, player_id, room.code)
        room.set_connection(player_id, conn_id)
        await persistence.upsert_player(player_id, name)
        await self._send_joined(conn_id, room, player_id)
        await self._broadcast_room(room)

    async def _on_join_room(self, conn_id: str, msg: dict) -> None:
        name = sanitize_name(msg.get("name"))
        player_id = self._ensure_player_id(conn_id, msg)
        code = str(msg.get("room_code") or "").strip().upper()
        room = self.rooms.join(code, player_id, name)
        self._bind(conn_id, player_id, room.code)
        room.set_connection(player_id, conn_id)
        await persistence.upsert_player(player_id, name)
        await self._send_joined(conn_id, room, player_id)
        await self._broadcast_room(room)

    async def _on_reconnect(self, conn_id: str, msg: dict) -> None:
        player_id = str(msg.get("player_id") or "").strip()
        code = str(msg.get("room_code") or "").strip().upper()
        room = self.rooms.get(code)
        if not room or not room.get_player(player_id):
            await self.connections.send(
                conn_id,
                {"type": "error", "code": "not_found", "message": "No session to reconnect to."},
            )
            return
        self._bind(conn_id, player_id, room.code)
        room.set_connection(player_id, conn_id)
        # Re-enter live gameplay if a match is running.
        if room.engine and room.state == "playing":
            room.engine.add_player(player_id, room.get_player(player_id)["name"])
        await self._send_joined(conn_id, room, player_id)
        await self._broadcast_room(room)

    async def _on_leave_room(self, conn_id: str, msg: dict) -> None:
        binding = self._bindings.pop(conn_id, None)
        if not binding:
            return
        room = self.rooms.get(binding["room_code"])
        if not room:
            return
        room.leave(binding["player_id"])
        room.clear_connection(conn_id)
        if room.count_connected() == 0:
            self.rooms.remove(room.code)
            self._match_tasks.pop(room.code, None)
            return
        await self._broadcast_room(room)

    async def _on_start_match(self, conn_id: str, msg: dict) -> None:
        room = self._room_for(conn_id)
        if not room:
            return
        player_id = self._bindings[conn_id]["player_id"]
        if room.get_player(player_id)["is_host"] is not True and player_id != room.host_id:
            await self.connections.send(
                conn_id, {"type": "error", "code": "not_host", "message": "Only the host can start the match."}
            )
            return
        if room.code in self._match_tasks:
            return  # already counting down / playing
        room.start_countdown()
        await self._broadcast_room(room)
        task = asyncio.get_running_loop().create_task(self._run_countdown_and_match(room))
        self._match_tasks[room.code] = task

    async def _on_play_again(self, conn_id: str, msg: dict) -> None:
        room = self._room_for(conn_id)
        if not room or room.state != "ended":
            return
        room.restart_for_rematch()
        await self._broadcast_room(room)
        room.start_countdown()
        task = asyncio.get_running_loop().create_task(self._run_countdown_and_match(room))
        self._match_tasks[room.code] = task

    async def _on_return_lobby(self, conn_id: str, msg: dict) -> None:
        room = self._room_for(conn_id)
        if not room:
            return
        room.return_to_lobby()
        self._match_tasks.pop(room.code, None)
        await self._broadcast_room(room)

    # ---- gameplay handlers (validated before touching the engine)
    async def _on_move(self, conn_id: str, msg: dict) -> None:
        room, player_id = self._room_and_player(conn_id)
        if not room or not room.engine:
            return
        room.engine.set_input(
            player_id, float(msg.get("x", 0)), float(msg.get("y", 0)), float(msg.get("angle", 0))
        )

    async def _on_shoot(self, conn_id: str, msg: dict) -> None:
        room, player_id = self._room_and_player(conn_id)
        if not room or not room.engine:
            return
        room.engine.fire(player_id, float(msg.get("angle", 0)))

    async def _on_ping(self, conn_id: str, msg: dict) -> None:
        await self.connections.send(
            conn_id, {"type": "pong", "client_time": msg.get("client_time")}
        )

    # ---------------------------------------------------------- match loop
    async def _run_countdown_and_match(self, room: Room) -> None:
        try:
            for remaining in range(room.countdown_remaining, 0, -1):
                await self._broadcast(room, {"type": "match_countdown", "seconds": remaining})
                await asyncio.sleep(1.0)

            if room.count_connected() < C.MIN_PLAYERS_TO_START:
                room.return_to_lobby()
                await self._broadcast(room, {"type": "match_aborted", "reason": "Not enough players."})
                return

            room.start_match()
            await self._broadcast(
                room,
                {
                    "type": "match_started",
                    "match_id": room.match_id,
                    "duration": C.MATCH_DURATION,
                    "arena": {"width": C.ARENA_WIDTH, "height": C.ARENA_HEIGHT},
                },
            )

            loop = asyncio.get_running_loop()
            while room.state == "playing" and room.engine is not None:
                t0 = loop.time()
                try:
                    room.engine.update(TICK_DELTA)
                    for ev in room.engine.drain_events():
                        await self._broadcast(room, {"type": "event", "event": ev})
                    if room.engine.state == "ended":
                        await self._finish_match(room)
                        return
                    await self._broadcast(room, {"type": "snapshot", "snapshot": room.engine.snapshot()})
                except Exception:  # noqa: BLE001 - never let one bad tick freeze the match
                    log.exception("Match %s crashed on a tick", room.code)
                    room.return_to_lobby()
                    await self._broadcast(room, {"type": "match_aborted", "reason": "Match error."})
                    return
                elapsed = loop.time() - t0
                await asyncio.sleep(max(0.0, TICK_DELTA - elapsed))
        except asyncio.CancelledError:
            pass
        finally:
            self._match_tasks.pop(room.code, None)

    async def _finish_match(self, room: Room) -> None:
        room.state = "ended"
        results = room.engine.results()
        for result in results:
            try:
                await persistence.record_match_result(room.code, result)
            except Exception:  # noqa: BLE001 - persistence must not break the UI
                log.exception("Failed to persist match result")
        await self._broadcast(room, {"type": "match_ended", "results": results})

    # ---------------------------------------------------------- helpers
    def _ensure_player_id(self, conn_id: str, msg: dict) -> str:
        # Use the client-provided id if present, else generate one server-side.
        pid = str(msg.get("player_id") or "").strip()
        if not pid:
            pid = conn_id
        return pid

    def _bind(self, conn_id: str, player_id: str, room_code: str) -> None:
        self._bindings[conn_id] = {"player_id": player_id, "room_code": room_code}

    def _room_for(self, conn_id: str) -> Room | None:
        binding = self._bindings.get(conn_id)
        if not binding:
            return None
        return self.rooms.get(binding["room_code"])

    def _room_and_player(self, conn_id: str) -> tuple[Room | None, str | None]:
        binding = self._bindings.get(conn_id)
        if not binding:
            return None, None
        room = self.rooms.get(binding["room_code"])
        return room, binding["player_id"]

    async def _send_joined(self, conn_id: str, room: Room, player_id: str) -> None:
        await self.connections.send(
            conn_id,
            {
                "type": "joined_room",
                "room_code": room.code,
                "state": room.state,
                "player_id": player_id,
                "players": room.player_list(),
            },
        )

    async def _broadcast_room(self, room: Room) -> None:
        if room.state in ("lobby", "ended", "countdown"):
            await self._broadcast(room, {"type": "room_update", **room.to_snapshot()})

    async def _broadcast(self, room: Room, payload: dict) -> None:
        await self.connections.send_many(room.connected_conn_ids(), payload)
