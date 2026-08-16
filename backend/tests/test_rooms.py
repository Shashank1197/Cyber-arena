#!/usr/bin/env python3
"""Unit tests for room lifecycle management."""
import pytest

from app.game import constants as C
from app.rooms.room import RoomError, RoomManager


def test_create_room():
    rm = RoomManager()
    room = rm.create("host1", "Host")
    assert len(room.code) == C.ROOM_CODE_LENGTH
    assert room.host_id == "host1"
    assert room.count_connected() == 1


def test_join_room():
    rm = RoomManager()
    room = rm.create("host1", "Host")
    joined = rm.join(room.code, "p2", "Player2")
    assert joined is room
    assert room.count_connected() == 2


def test_invalid_room_code_raises():
    rm = RoomManager()
    with pytest.raises(RoomError) as exc:
        rm.join("ZZZZZZ", "p2", "Player2")
    assert exc.value.code == "not_found"


def test_room_is_full():
    rm = RoomManager()
    room = rm.create("h", "H")
    for i in range(C.MAX_PLAYERS - 1):
        room.add_player(f"p{i}", f"P{i}")
    with pytest.raises(RoomError) as exc:
        room.add_player("overflow", "Overflow")
    assert exc.value.code == "full"


def test_cannot_join_match_in_progress():
    rm = RoomManager()
    room = rm.create("h", "H")
    room.add_player("p2", "P2")
    room.start_countdown()
    room.state = "playing"  # simulate a live match
    with pytest.raises(RoomError) as exc:
        room.add_player("p3", "P3")
    assert exc.value.code == "match_started"


def test_leave_promotes_new_host():
    rm = RoomManager()
    room = rm.create("host1", "Host")
    room.add_player("p2", "Player2")
    room.leave("host1")
    assert room.get_player("p2")["is_host"] is True


def test_player_disconnect_is_tracked():
    rm = RoomManager()
    room = rm.create("host1", "Host")
    room.add_player("p2", "Player2")
    room.set_connection("p2", "conn2")
    room.clear_connection("conn2")
    assert room.get_player("p2")["connected"] is False
    assert room.count_connected() == 1


def test_start_requires_two_players():
    rm = RoomManager()
    room = rm.create("host1", "Host")
    with pytest.raises(RoomError) as exc:
        room.start_countdown()
    assert exc.value.code == "not_enough_players"
