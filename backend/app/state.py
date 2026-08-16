#!/usr/bin/env python3
"""Application-wide singletons shared between the REST API and WebSocket layer.
"""
from .game.server import GameServer

# Single GameServer instance drives all rooms and matches in this process.
game_server = GameServer()
