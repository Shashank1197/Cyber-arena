#!/usr/bin/env python3
"""Static arena layout: perimeter, interior obstacles, capture nodes, spawns.

The arena is a 1600x1000 box. Obstacles are placed to create a centre "ring"
with chokepoints and corridors, while capture nodes sit around the mid-ring and
in the open corners, encouraging movement between objectives.
"""
from __future__ import annotations

from .constants import (
    ARENA_HEIGHT,
    ARENA_WIDTH,
    NODE_CAPTURE_RADIUS,
)
from .geometry import Rect

PLAYER_COLORS = ["#00f0ff", "#ff2e6f", "#ffd23f", "#7cff4f"]

# Interior solid obstacles (axis-aligned boxes).
def build_obstacles() -> list[Rect]:
    return [
        Rect(400, 380, 120, 240),   # left mid vertical
        Rect(1080, 380, 120, 240),  # right mid vertical
        Rect(700, 110, 200, 110),   # top mid horizontal
        Rect(700, 780, 200, 110),   # bottom mid horizontal
        Rect(748, 458, 104, 84),    # centre block
        Rect(170, 170, 70, 70),     # small top-left
        Rect(1360, 170, 70, 70),    # small top-right
        Rect(170, 760, 70, 70),     # small bottom-left
        Rect(1360, 760, 70, 70),    # small bottom-right
    ]


def build_nodes() -> list[dict]:
    return [
        {"id": "node_a", "x": 210, "y": 500},
        {"id": "node_b", "x": 1390, "y": 500},
        {"id": "node_c", "x": 800, "y": 262},
        {"id": "node_d", "x": 800, "y": 738},
    ]


def build_spawns() -> list[tuple[float, float]]:
    margin = 90
    return [
        (margin, margin),
        (ARENA_WIDTH - margin, margin),
        (margin, ARENA_HEIGHT - margin),
        (ARENA_WIDTH - margin, ARENA_HEIGHT - margin),
    ]


def valid_open_position(obstacles, x, y, radius, tries=40) -> tuple[float, float]:
    """Return a point inside the arena that does not overlap an obstacle."""
    import random

    from .geometry import circle_rect_collide

    for _ in range(tries):
        if not circle_rect_collide(x, y, radius, obstacles):
            return (x, y)
        x = random.uniform(NODE_CAPTURE_RADIUS, ARENA_WIDTH - NODE_CAPTURE_RADIUS)
        y = random.uniform(NODE_CAPTURE_RADIUS, ARENA_HEIGHT - NODE_CAPTURE_RADIUS)
    return (ARENA_WIDTH / 2.0, ARENA_HEIGHT / 2.0)
