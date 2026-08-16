#!/usr/bin/env python3
"""Room lifecycle: creation, joining, leaving, match state.

A Room holds the players that belong to it (identified by client-generated
player ids so reconnects are possible) plus the match state machine:
lobby -> countdown -> playing -> ended. The GameServer drives the transition
and the simulation; this module owns the invariants and validation.
"""
from __future__ import annotations

import random
import time
from typing import Optional

from ..game import constants as C
from ..game.engine import GameEngine

_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no ambiguous 0/O, 1/I


class RoomError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _random_code() -> str:
    return "".join(random.choice(_ALPHABET) for _ in range(C.ROOM_CODE_LENGTH))


class Room:
    def __init__(self, code: str, host_id: str, host_name: str) -> None:
        self.code = code
        self.host_id = host_id
        self.created_at = time.time()
        # player_id -> player record
        self.players: dict[str, dict] = {}
        self._add_player(host_id, host_name, is_host=True)

        self.state = "lobby"  # lobby | countdown | playing | ended
        self.engine: Optional[GameEngine] = None
        self.match_id: Optional[str] = None
        self.countdown_remaining: int = 0
        self.match_started_at: float = 0.0

    def _add_player(self, player_id: str, name: str, is_host: bool = False) -> None:
        self.players[player_id] = {
            "id": player_id,
            "name": name,
            "connected": True,
            "conn_id": None,
            "is_host": is_host,
            "joined_at": time.time(),
        }

    # ------------------------------------------------------------- queries
    def connected_conn_ids(self) -> list[str]:
        return [p["conn_id"] for p in self.players.values() if p["conn_id"]]

    def player_list(self) -> list[dict]:
        return [
            {
                "id": p["id"],
                "name": p["name"],
                "connected": p["connected"],
                "is_host": p["is_host"],
            }
            for p in self.players.values()
        ]

    def get_player(self, player_id: str) -> Optional[dict]:
        return self.players.get(player_id)

    def set_connection(self, player_id: str, conn_id: str) -> None:
        p = self.players.get(player_id)
        if p:
            p["conn_id"] = conn_id
            p["connected"] = True

    def clear_connection(self, conn_id: str) -> None:
        for p in self.players.values():
            if p["conn_id"] == conn_id:
                p["conn_id"] = None
                p["connected"] = False

    def count_connected(self) -> int:
        return sum(1 for p in self.players.values() if p["connected"])

    def mark_connected(self, player_id: str) -> None:
        p = self.players.get(player_id)
        if p:
            p["connected"] = True

    # ------------------------------------------------------------- actions
    def add_player(self, player_id: str, name: str) -> None:
        if player_id in self.players:
            return
        if len(self.players) >= C.MAX_PLAYERS:
            raise RoomError("full", "Room is full (max 4 players).")
        if self.state not in ("lobby", "ended"):
            raise RoomError("match_started", "Match already in progress.")
        self._add_player(player_id, name)

    def remove_player(self, player_id: str) -> Optional[dict]:
        return self.players.pop(player_id, None)

    def leave(self, player_id: str) -> None:
        removed = self.players.pop(player_id, None)
        if removed and removed["is_host"] and self.players:
            # Promote the oldest remaining connected player to host.
            for other in self.players.values():
                other["is_host"] = True
                break
        # Release the player's in-game presence.
        if self.engine:
            self.engine.remove_player(player_id)

    # ------------------------------------------------------------- match
    def start_countdown(self) -> None:
        if self.state != "lobby":
            raise RoomError("match_started", "Match already in progress.")
        if self.count_connected() < C.MIN_PLAYERS_TO_START:
            raise RoomError("not_enough_players", "Need at least 2 players.")
        self.state = "countdown"
        self.countdown_remaining = C.COUNTDOWN_SECONDS

    def start_match(self) -> None:
        self.match_id = f"m_{self.code}_{int(time.time())}"
        meta = [
            {"id": p["id"], "name": p["name"]}
            for p in self.players.values()
            if p["connected"]
        ]
        self.engine = GameEngine(self.match_id, meta)
        self.state = "playing"
        self.match_started_at = time.time()

    def restart_for_rematch(self) -> None:
        # Reset per-player match statistics, then start a fresh countdown.
        self.engine = None
        self.match_id = None
        self.state = "lobby"

    def return_to_lobby(self) -> None:
        self.engine = None
        self.match_id = None
        self.state = "lobby"

    def to_snapshot(self) -> dict:
        return {
            "room_code": self.code,
            "state": self.state,
            "players": self.player_list(),
            "host_id": self.host_id,
        }


class RoomManager:
    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}

    def create(self, host_id: str, host_name: str) -> Room:
        for _ in range(200):
            code = _random_code()
            if code not in self._rooms:
                room = Room(code, host_id, host_name)
                self._rooms[code] = room
                return room
        raise RoomError("internal", "Could not allocate a room code.")

    def get(self, code: str) -> Optional[Room]:
        code = code.strip().upper()
        return self._rooms.get(code)

    def join(self, code: str, player_id: str, name: str) -> Room:
        room = self.get(code)
        if room is None:
            raise RoomError("not_found", "Invalid room code.")
        room.add_player(player_id, name)
        return room

    def remove(self, code: str) -> None:
        self._rooms.pop(code, None)

    def active_rooms(self) -> list[Room]:
        return list(self._rooms.values())
