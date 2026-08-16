#!/usr/bin/env python3
"""Minimal 2D geometry helpers for the arena simulation.

Kept intentionally tiny and dependency-free. We only need axis-aligned
rectangles and circles (players/projectiles/nodes).
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.h

    def center(self) -> tuple[float, float]:
        return (self.x + self.w / 2.0, self.y + self.h / 2.0)

    def contains(self, px: float, py: float) -> bool:
        return self.left <= px <= self.right and self.top <= py <= self.bottom

    def closest_point(self, px: float, py: float) -> tuple[float, float]:
        """Closest point on the rectangle boundary to a given point."""
        cx = max(self.left, min(px, self.right))
        cy = max(self.top, min(py, self.bottom))
        return (cx, cy)

    def resolve_circle(self, cx: float, cy: float, radius: float) -> tuple[float, float]:
        """Push a circle out of the rectangle if it overlaps.

        Uses axis-of-least-penetration so movement along a wall stays smooth.
        Returns the corrected center position.
        """
        # Circle center is inside the rect -> push out through nearest face.
        if self.contains(cx, cy):
            push_left = cx - self.left
            push_right = self.right - cx
            push_top = cy - self.top
            push_bottom = self.bottom - cy
            m = min(push_left, push_right, push_top, push_bottom)
            if m == push_left:
                return (self.left - radius, cy)
            if m == push_right:
                return (self.right + radius, cy)
            if m == push_top:
                return (cx, self.top - radius)
            return (cx, self.bottom + radius)

        px, py = self.closest_point(cx, cy)
        dx = cx - px
        dy = cy - py
        dist2 = dx * dx + dy * dy
        if dist2 >= radius * radius:
            return (cx, cy)
        if dist2 == 0.0:
            return (cx, cy)
        dist = math.sqrt(dist2)
        ox = dx / dist * (radius - dist)
        oy = dy / dist * (radius - dist)
        return (cx + ox, cy + oy)


def circle_rect_collide(
    cx: float, cy: float, radius: float, rect: Rect
) -> bool:
    px, py = rect.closest_point(cx, cy)
    dx = cx - px
    dy = cy - py
    return dx * dx + dy * dy <= radius * radius


def dist2(ax: float, ay: float, bx: float, by: float) -> float:
    dx = ax - bx
    dy = ay - by
    return dx * dx + dy * dy

def normalize(dx: float, dy: float) -> tuple[float, float]:
    d = math.hypot(dx, dy)
    if d == 0.0:
        return (0.0, 0.0)
    return (dx / d, dy / d)
