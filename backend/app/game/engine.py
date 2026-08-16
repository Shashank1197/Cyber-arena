#!/usr/bin/env python3
"""Authoritative game engine.

The engine owns the full simulation and is the single source of truth for every
outcome in a match: movement, projectiles, collisions, damage, kills, node
capture, power-ups and score. The browser only sends *intentions* (move
direction, aim angle, fire); every result is computed here.

A single tick is driven by :meth:`update`. Side effects that should be
broadcast to clients are appended to :attr:`events` (a drainable list), so the
I/O layer stays dumb and the engine stays testable in isolation.
"""
from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from typing import Optional

from . import constants as C
from .geometry import Rect, circle_rect_collide
from .map import (
    PLAYER_COLORS,
    build_nodes,
    build_obstacles,
    build_spawns,
    valid_open_position,
)
from .models import CaptureNode, Player, PowerUp, Projectile


@dataclass
class KillEvent:
    killer_id: str
    victim_id: str


class GameEngine:
    def __init__(
        self,
        match_id: str,
        players_meta: list[dict],
        duration: float = C.MATCH_DURATION,
    ) -> None:
        self.match_id = match_id
        self.duration = duration
        self.time = 0.0
        self.state = "playing"

        self.obstacles: list[Rect] = build_obstacles()
        self.spawns: list[tuple[float, float]] = build_spawns()
        self.nodes: list[CaptureNode] = [
            CaptureNode(id=n["id"], x=n["x"], y=n["y"], radius=C.NODE_CAPTURE_RADIUS)
            for n in build_nodes()
        ]
        self.players: dict[str, Player] = {}
        self.projectiles: dict[str, Projectile] = {}
        self.powerups: list[PowerUp] = []

        self.events: list[dict] = []
        self._next_id = 0
        self._powerup_timer = 0.0
        self._wall_bounds = Rect(0, 0, C.ARENA_WIDTH, C.ARENA_HEIGHT)

        for idx, meta in enumerate(players_meta):
            self._add_player(meta["id"], meta["name"], idx)

    # ------------------------------------------------------------------ ids
    def _new_id(self, prefix: str) -> str:
        self._next_id += 1
        return f"{prefix}_{self.match_id}_{self._next_id}"

    # -------------------------------------------------------------- players
    def _add_player(self, pid: str, name: str, idx: int) -> None:
        sx, sy = self.spawns[idx % len(self.spawns)]
        self.players[pid] = Player(
            id=pid,
            name=name,
            x=sx,
            y=sy,
            color=PLAYER_COLORS[idx % len(PLAYER_COLORS)],
        )

    def add_player(self, pid: str, name: str) -> None:
        idx = len(self.players)
        self._add_player(pid, name, idx)

    def remove_player(self, pid: str) -> None:
        player = self.players.pop(pid, None)
        if player is None:
            return
        self.events.append({"type": "player_removed", "player_id": pid})
        # Remove this player's projectiles from the field.
        self.projectiles = {
            k: p for k, p in self.projectiles.items() if p.owner_id != pid
        }
        # If they owned nodes, release them back to neutral.
        for node in self.nodes:
            if node.owner_id == pid:
                node.owner_id = None
                node.progress = 0.0

    def set_input(self, pid: str, move_x: float, move_y: float, angle: float) -> None:
        player = self.players.get(pid)
        if not player:
            return
        if not player.alive:
            player.move_x = 0.0
            player.move_y = 0.0
            return
        player.move_x = max(-1.0, min(1.0, move_x))
        player.move_y = max(-1.0, min(1.0, move_y))
        if isinstance(angle, (int, float)) and math.isfinite(angle):
            player.angle = float(angle) % (2 * math.pi)

    def fire(self, pid: str, angle: float) -> None:
        player = self.players.get(pid)
        if not player or not player.alive or player.fire_cooldown > 0:
            return
        if not isinstance(angle, (int, float)) or not math.isfinite(angle):
            angle = player.angle
        angle = float(angle) % (2 * math.pi)
        player.angle = angle
        player.fire_cooldown = C.FIRE_COOLDOWN

        ox = math.cos(angle)
        oy = math.sin(angle)
        start_x = player.x + ox * (C.PLAYER_RADIUS + 4)
        start_y = player.y + oy * (C.PLAYER_RADIUS + 4)
        proj = Projectile(
            id=self._new_id("b"),
            owner_id=pid,
            x=start_x,
            y=start_y,
            vx=ox * C.PROJECTILE_SPEED,
            vy=oy * C.PROJECTILE_SPEED,
            damage=C.PROJECTILE_DAMAGE * player.damage_mult(),
            angle=angle,
            ttl=C.PROJECTILE_TTL,
        )
        self.projectiles[proj.id] = proj
        self.events.append(
            {
                "type": "bullet_spawn",
                "id": proj.id,
                "owner_id": pid,
                "x": proj.x,
                "y": proj.y,
                "vx": proj.vx,
                "vy": proj.vy,
                "angle": proj.angle,
                "damage": proj.damage,
            }
        )

    # -------------------------------------------------------------- update
    def update(self, dt: float) -> None:
        if self.state != "playing":
            return
        dt = max(0.0, min(dt, 0.1))
        self.time += dt
        self._tick_cooldowns(dt)
        self._move_players(dt)
        self._update_projectiles(dt)
        self._update_capture(dt)
        self._update_powerups(dt)
        self._update_score(dt)
        self._update_respawns(dt)
        self._check_state()

    def _tick_cooldowns(self, dt: float) -> None:
        for player in self.players.values():
            if player.fire_cooldown > 0:
                player.fire_cooldown = max(0.0, player.fire_cooldown - dt)

    def _move_players(self, dt: float) -> None:
        for player in self.players.values():
            if not player.alive:
                continue
            speed = C.PLAYER_SPEED * player.speed_mult()
            nx = player.x + player.move_x * speed * dt
            ny = player.y + player.move_y * speed * dt
            nx, ny = self._resolve_collisions(nx, ny, C.PLAYER_RADIUS)
            player.x, player.y = nx, ny

    def _resolve_collisions(self, x: float, y: float, radius: float) -> tuple[float, float]:
        # Arena walls.
        x = max(radius, min(x, C.ARENA_WIDTH - radius))
        y = max(radius, min(y, C.ARENA_HEIGHT - radius))
        # Interior obstacles.
        for rect in self.obstacles:
            x, y = rect.resolve_circle(x, y, radius)
        return x, y

    def _update_projectiles(self, dt: float) -> None:
        dead: list[str] = []
        for proj in self.projectiles.values():
            proj.x += proj.vx * dt
            proj.y += proj.vy * dt
            proj.ttl -= dt
            # Wall / bounds.
            if (
                proj.ttl <= 0
                or proj.x < 0
                or proj.x > C.ARENA_WIDTH
                or proj.y < 0
                or proj.y > C.ARENA_HEIGHT
            ):
                dead.append(proj.id)
                continue
            # Obstacles.
            hit_obstacle = any(
                circle_rect_collide(proj.x, proj.y, C.PROJECTILE_RADIUS, rect)
                for rect in self.obstacles
            )
            if hit_obstacle:
                dead.append(proj.id)
                continue
            # Player hits.
            for player in self.players.values():
                if (
                    player.alive
                    and player.id != proj.owner_id
                    and math.hypot(player.x - proj.x, player.y - proj.y)
                    <= C.PLAYER_RADIUS + C.PROJECTILE_RADIUS
                ):
                    self._apply_damage(player.id, proj.owner_id, proj.damage)
                    dead.append(proj.id)
                    break
        for pid in dead:
            self.projectiles.pop(pid, None)
            self.events.append({"type": "bullet_remove", "id": pid})

    def _apply_damage(self, target_id: str, attacker_id: str, damage: float) -> None:
        target = self.players.get(target_id)
        if not target or not target.alive:
            return
        damage *= target.incoming_damage_mult()
        target.health = max(0.0, target.health - damage)
        self.events.append(
            {
                "type": "player_damaged",
                "target_id": target_id,
                "attacker_id": attacker_id,
                "damage": damage,
                "health": target.health,
            }
        )
        if target.health <= 0.0:
            self._kill(target_id, attacker_id)

    def _kill(self, victim_id: str, killer_id: str) -> None:
        victim = self.players.get(victim_id)
        killer = self.players.get(killer_id)
        if not victim:
            return
        victim.alive = False
        victim.respawn_in = C.RESPAWN_DELAY
        victim.deaths += 1
        victim.effects.clear()
        if killer and killer_id != victim_id:
            killer.kills += 1
            killer.score += C.KILL_SCORE
        self.events.append(
            {
                "type": "player_killed",
                "killer_id": killer_id,
                "victim_id": victim_id,
            }
        )

    def _update_respawns(self, dt: float) -> None:
        for player in self.players.values():
            if player.alive:
                continue
            player.respawn_in -= dt
            if player.respawn_in <= 0:
                sx, sy = self._pick_spawn()
                player.x, player.y = sx, sy
                player.health = C.MAX_HEALTH
                player.alive = True
                player.effects.clear()
                player.move_x = 0.0
                player.move_y = 0.0
                self.events.append(
                    {"type": "player_respawned", "player_id": player.id, "x": sx, "y": sy}
                )

    def _pick_spawn(self) -> tuple[float, float]:
        candidates = list(self.spawns)
        random.shuffle(candidates)
        for sx, sy in candidates:
            if all(
                math.hypot(p.x - sx, p.y - sy) > C.PLAYER_RADIUS * 3
                for p in self.players.values()
                if p.alive
            ):
                return sx, sy
        return candidates[0]

    # -------------------------------------------------------------- capture
    def _update_capture(self, dt: float) -> None:
        for node in self.nodes:
            nearby: list[Player] = [
                p for p in self.players.values() if p.alive and p.connected
                and math.hypot(p.x - node.x, p.y - node.y) <= node.radius
            ]
            distinct = {p.id for p in nearby}
            node.contested = len(distinct) > 1

            if not nearby:
                continue

            if node.owner_id is None:
                # Neutral: only capture if exactly one distinct player present.
                if len(distinct) == 1:
                    capturer = nearby[0]
                    node.progress = min(100.0, node.progress + C.NODE_CAPTURE_RATE * dt)
                    if node.progress >= 100.0:
                        self._assign_node(node, capturer.id)
            else:
                owner = self.players.get(node.owner_id)
                enemies = [p for p in nearby if p.id != node.owner_id]
                if enemies and len(distinct) > 1:
                    # Multiple captors fighting -> contest, no change.
                    continue
                if enemies:
                    # Single enemy contesting: drain ownership back to neutral.
                    node.progress = max(0.0, node.progress - C.NODE_CONTEST_RATE * dt)
                    if node.progress <= 0.0:
                        node.owner_id = None

    def _assign_node(self, node: CaptureNode, pid: str) -> None:
        node.owner_id = pid
        node.progress = 100.0
        self.players[pid].nodes_captured += 1
        self.events.append(
            {"type": "node_captured", "node_id": node.id, "owner_id": pid}
        )

    # -------------------------------------------------------------- powerups
    def _update_powerups(self, dt: float) -> None:
        self._powerup_timer += dt
        if (
            self._powerup_timer >= C.POWERUP_SPAWN_INTERVAL
            and len(self.powerups) < C.POWERUP_MAX_ACTIVE
        ):
            self._powerup_timer = 0.0
            self._spawn_powerup()

        remaining: list[PowerUp] = []
        for pu in self.powerups:
            pu.ttl -= dt
            if pu.ttl <= 0:
                self.events.append({"type": "powerup_removed", "id": pu.id})
                continue
            # Collection.
            collected = None
            for player in self.players.values():
                if player.alive and math.hypot(player.x - pu.x, player.y - pu.y) <= C.PLAYER_RADIUS + 14:
                    collected = player
                    break
            if collected:
                collected.effects[pu.type] = C.POWERUP_DURATION
                self.events.append(
                    {
                        "type": "powerup_collected",
                        "player_id": collected.id,
                        "id": pu.id,
                        "powerup_type": pu.type,
                    }
                )
                continue
            remaining.append(pu)
        self.powerups = remaining

        # Decay active effects.
        for player in self.players.values():
            for kind in list(player.effects):
                player.effects[kind] -= dt
                if player.effects[kind] <= 0:
                    del player.effects[kind]

    def _spawn_powerup(self) -> None:
        x = random.uniform(C.NODE_CAPTURE_RADIUS, C.ARENA_WIDTH - C.NODE_CAPTURE_RADIUS)
        y = random.uniform(C.NODE_CAPTURE_RADIUS, C.ARENA_HEIGHT - C.NODE_CAPTURE_RADIUS)
        x, y = valid_open_position(self.obstacles, x, y, 24)
        pu = PowerUp(
            id=self._new_id("p"),
            x=x,
            y=y,
            type=random.choice(C.POWERUP_TYPES),
            ttl=C.POWERUP_GROUND_TTL,
        )
        self.powerups.append(pu)
        self.events.append(
            {"type": "powerup_spawned", "id": pu.id, "x": pu.x, "y": pu.y, "powerup_type": pu.type}
        )

    # -------------------------------------------------------------- score
    def _update_score(self, dt: float) -> None:
        for node in self.nodes:
            if node.owner_id and node.owner_id in self.players:
                self.players[node.owner_id].score += C.NODE_SCORE_RATE * dt

    # -------------------------------------------------------------- state
    def _check_state(self) -> None:
        if self.time >= self.duration:
            self.state = "ended"
            return
        for player in self.players.values():
            if player.score >= C.SCORE_CAP:
                self.state = "ended"
                return
        # A player who owns every node instantly captures the arena.
        total = len(self.nodes)
        if total > 0:
            for player in self.players.values():
                owned = sum(1 for n in self.nodes if n.owner_id == player.id)
                if owned >= total:
                    self.state = "ended"
                    return

    # -------------------------------------------------------------- output
    def snapshot(self) -> dict:
        return {
            "t": round(self.time, 3),
            "state": self.state,
            "time_left": round(max(0.0, self.duration - self.time), 1),
            "players": [
                {
                    "id": p.id,
                    "name": p.name,
                    "x": round(p.x, 1),
                    "y": round(p.y, 1),
                    "angle": round(p.angle, 3),
                    "health": round(p.health, 1),
                    "alive": p.alive,
                    "respawn_in": round(max(0.0, p.respawn_in), 1),
                    "score": round(p.score),
                    "kills": p.kills,
                    "deaths": p.deaths,
                    "color": p.color,
                    "effects": list(p.effects.keys()),
                }
                for p in self.players.values()
            ],
            "nodes": [
                {
                    "id": n.id,
                    "x": round(n.x, 1),
                    "y": round(n.y, 1),
                    "owner_id": n.owner_id,
                    "progress": round(n.progress, 1),
                    "contested": n.contested,
                }
                for n in self.nodes
            ],
            "powerups": [
                {"id": p.id, "x": round(p.x, 1), "y": round(p.y, 1), "type": p.type}
                for p in self.powerups
            ],
            "projectiles": [
                {
                    "id": p.id,
                    "owner_id": p.owner_id,
                    "x": round(p.x, 1),
                    "y": round(p.y, 1),
                    "angle": round(p.angle, 3),
                    "damage": round(p.damage, 1),
                }
                for p in self.projectiles.values()
                if p.alive
            ],
        }

    def results(self) -> list[dict]:
        return [
            {
                "player_id": p.id,
                "player_name": p.name,
                "score": round(p.score),
                "kills": p.kills,
                "deaths": p.deaths,
                "nodes_captured": p.nodes_captured,
                "match_duration": round(self.time, 1),
            }
            for p in self.players.values()
        ]

    def drain_events(self) -> list[dict]:
        events = self.events
        self.events = []
        return events
