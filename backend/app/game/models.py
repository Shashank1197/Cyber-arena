#!/usr/bin/env python3
"""In-memory data models for the authoritative game simulation.

These are pure-Python dataclasses. They live only in server RAM while a match
is running and are never written to the database.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Player:
    id: str
    name: str
    x: float
    y: float
    angle: float = 0.0
    health: float = 100.0
    alive: bool = True
    respawn_in: float = 0.0
    score: float = 0.0
    kills: int = 0
    deaths: int = 0
    nodes_captured: int = 0
    fire_cooldown: float = 0.0
    move_x: float = 0.0
    move_y: float = 0.0
    connected: bool = True
    color: str = "#00f0ff"
    effects: dict[str, float] = field(default_factory=dict)  # type -> remaining s

    def speed_mult(self) -> float:
        from .constants import SPEED_BOOST_MULT
        return SPEED_BOOST_MULT if "speed" in self.effects else 1.0

    def damage_mult(self) -> float:
        from .constants import OVERCHARGE_DAMAGE_MULT
        return OVERCHARGE_DAMAGE_MULT if "overcharge" in self.effects else 1.0

    def incoming_damage_mult(self) -> float:
        from .constants import SHIELD_DAMAGE_MULT
        return SHIELD_DAMAGE_MULT if "shield" in self.effects else 1.0


@dataclass
class Projectile:
    id: str
    owner_id: str
    x: float
    y: float
    vx: float
    vy: float
    damage: float
    angle: float
    ttl: float
    alive: bool = True


@dataclass
class CaptureNode:
    id: str
    x: float
    y: float
    radius: float
    owner_id: Optional[str] = None
    progress: float = 0.0
    contested: bool = False


@dataclass
class PowerUp:
    id: str
    x: float
    y: float
    type: str
    ttl: float


@dataclass
class MatchResult:
    player_id: str
    player_name: str
    score: float
    kills: int
    deaths: int
    nodes_captured: int
    match_duration: float

    def to_dict(self) -> dict:
        return {
            "player_id": self.player_id,
            "player_name": self.player_name,
            "score": self.score,
            "kills": self.kills,
            "deaths": self.deaths,
            "nodes_captured": self.nodes_captured,
            "match_duration": self.match_duration,
        }
