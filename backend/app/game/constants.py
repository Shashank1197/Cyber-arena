#!/usr/bin/env python3
"""Central, authoritative game-tuning constants.

These values are used by the server to run the simulation. The browser mirrors
most of them (see frontend/src/game/constants.ts) purely for rendering and
local-prediction purposes; the server is always the source of truth.
"""

# --- Arena ---
ARENA_WIDTH = 1600
ARENA_HEIGHT = 1000

# --- Player ---
PLAYER_RADIUS = 16.0
PLAYER_SPEED = 230.0
MAX_HEALTH = 100.0
RESPAWN_DELAY = 2.5
FIRE_COOLDOWN = 0.22

# --- Projectiles ---
PROJECTILE_SPEED = 560.0
PROJECTILE_RADIUS = 5.0
PROJECTILE_DAMAGE = 14.0
PROJECTILE_TTL = 2.0

# --- Scoring ---
KILL_SCORE = 100.0
NODE_SCORE_RATE = 1.0  # points per second per owned node

# --- Capture nodes ---
NODE_CAPTURE_RADIUS = 70.0
NODE_RENDER_RADIUS = 34.0
NODE_CAPTURE_RATE = 30.0  # neutral -> player progress per second
NODE_CONTEST_RATE = 30.0  # enemy progress drain per second

# --- Match ---
MAX_PLAYERS = 4
MIN_PLAYERS_TO_START = 2
MATCH_DURATION = 180.0
SCORE_CAP = 2000.0
COUNTDOWN_SECONDS = 3

# --- Power-ups ---
POWERUP_TYPES = ("speed", "shield", "overcharge")
POWERUP_SPAWN_INTERVAL = 6.0
POWERUP_MAX_ACTIVE = 3
POWERUP_GROUND_TTL = 12.0
POWERUP_DURATION = 8.0
SPEED_BOOST_MULT = 1.5
SHIELD_DAMAGE_MULT = 0.5
OVERCHARGE_DAMAGE_MULT = 1.5

# --- Tick / networking ---
TICK_RATE = 20  # server simulation ticks per second

# --- Room ---
ROOM_CODE_LENGTH = 6

# --- Reconnect ---
RECONNECT_WINDOW_SECONDS = 30.0
