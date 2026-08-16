# PROJECT DECISIONS

## What I built

Cyber Arena is a real-time multiplayer strategy/action game for 2–4 players.
Players join a room by code, fight inside a top-down arena to capture network
nodes and shoot each other, and win by scoring the most points before the match
timer expires. The backend is a FastAPI + WebSocket server that runs the whole
simulation authoritatively; the frontend is a React/TypeScript client that
renders the arena on HTML Canvas and only sends player intentions.

## Why I chose this project

The brief asked for something that is genuinely playable, not a demo. A
server-authoritative multiplayer game is a great fit because it forces good
systems engineering: a deterministic game loop, clean separation of network
I/O from simulation, a well-defined message protocol, and careful state
synchronization. It also has a clear, measurable "did it work" bar — several
browser windows playing a live match together.

## Problem / game concept

The core challenge in any real-time multiplayer game is making the server the
single source of truth while keeping the experience responsive. Cyber Arena
solves the "capture the point" genre with three interacting loops: movement and
combat, node capture, and the score economy. That's enough depth to be
interesting but simple enough to understand in under thirty seconds.

## Architecture

Two processes:

- **Backend** (`backend/app`): FastAPI exposes a REST API for health, the
  leaderboard, and match history, plus a WebSocket endpoint at `/ws`. A
  `GameServer` owns connections, rooms, and a match-loop task per active room.
  The simulation is split into focused modules: `GameEngine` (tick update),
  `CollisionSystem`-style helpers in `geometry.py`, capture and combat logic
  inside the engine, `Room`/`RoomManager` for lobby lifecycle, and a
  `PersistenceService` for MongoDB.
- **Frontend** (`frontend/src`): React drives the screen state machine
  (Home → Lobby → Game → Results). A `GameSocket`/`NetworkClient` layer handles
  the WebSocket with auto-reconnect. A `Renderer` draws the arena from the
  latest authoritative snapshot; a lightweight `ClientEngine` samples input and
  forwards intentions.

Key separation: **rendering**, **input**, **network**, and **game logic** are
isolated so the render loop never touches the network directly and vice versa.

## Why WebSockets

Real-time multiplayer needs a persistent, bidirectional, low-latency channel.
WebSockets give us a single long-lived connection that both the client (sending
move/shoot intentions at ~15–20 Hz) and the server (broadcasting snapshots and
events) can write to without the overhead of HTTP request/response round trips.
They are first-class in browsers and well supported by FastAPI, making them the
pragmatic choice for an MVP.

## Why server-authoritative architecture

Trusting the client for outcomes is how multiplayer games get broken and how
"fake multiplayer" demos hide their hand. In Cyber Arena the client only ever
sends *intentions* (move direction, aim angle, fire). The server validates every
message, runs the authoritative simulation, computes damage/kills/score/capture,
and broadcasts results. This means:

- A client cannot report "I killed Player 2" — it can only request a shot.
- Score, kills, node ownership, and match results are all computed server-side.
- Movement, fire rate, and inputs are clamped and validated server-side.

The engine is written to be testable in isolation: it drains a list of events
each tick, and the I/O layer just forwards them. This is what made the test
suite clean to write.

## Game-state design

Match state is a small, explicit state machine on the `Room`:

```
lobby → countdown → playing → ended (results)
```

`Room` owns the state machine and match lifecycle; `GameEngine` owns the
simulation while `playing`. Transitions (start countdown, start match, finish,
play-again, return-to-lobby) are centralized on `Room` and driven by the
`GameServer`, so state logic is not scattered across the codebase.

The live simulation lives only in server memory. `GameEngine` exposes a
`snapshot()` for periodic broadcast and `drain_events()` for discrete events
(kill, node captured, power-up). The client receives full snapshots at 20 Hz
and event messages, keeping bandwidth reasonable.

## Database decisions

Real-time game state is never written to MongoDB — it stays in memory for speed
and simplicity. MongoDB (via Motor) is used only for long-lived records:

- `players`: display-name registry
- `matches`: a record per match
- `match_results`: one row per player per match (score, kills, deaths, nodes)

To keep local development friction-free, `PersistenceService` transparently
falls back to an in-memory repository when `MONGO_URL` is unset, so the whole
game runs without a database installed.

## Important technical challenges

1. **Authoritative movement with smooth rendering.** The server integrates
   movement at 20 Hz; the client renders at 60 FPS. The client shows the latest
   server position with light interpolation so remote players don't jitter,
   while the local player is also reconciled to the server position.

2. **Collision resolution.** Used axis-of-least-penetration against a fixed
   rectangle obstacle set so a player sliding along a wall moves smoothly, and
   mirrored the same algorithm client-side for local prediction.

3. **Disconnect handling.** A sudden disconnect must not crash the match or
   leave a frozen ghost. On disconnect the player is removed from active
   gameplay immediately, a reconnect window keeps the slot, and the room is
   cleaned up (or promoted to a new host) after the window expires.

4. **Fixed-tick loop with broadcast pacing.** The match task runs at a fixed
   rate, advances the engine, drains events, and broadcasts a compact snapshot
   each tick. Timing uses the event-loop clock so drift is minimal.

## Trade-offs

- **No client-side prediction of position.** Kept the MVP reliable and
  cheat-resistant; the local player is authoritative-server-reconciled. Under
  very high latency this is slightly less smooth but far simpler and safer.
  Prediction can be added later (documented in improvements).
- **Single-process room storage.** Simplest correct approach; documented that
  horizontal scaling requires a shared pub/sub transport.
- **Fixed single map.** Focused effort on gameplay and netcode over content;
  maps are data-driven so adding more is straightforward.
- **In-memory fallback over requiring MongoDB.** Favors easy local dev; real
  persistence is available when configured.

## What I would improve

- Client-side prediction + server reconciliation for local movement.
- A spectator mode and match replay.
- Sound design and richer feedback (hit markers, kill cam).
- Multiple maps and map voting.
- Global matchmaking and persistent ranked leaderboards.
- Horizontal scaling via Redis pub/sub for room and match state.
- A WebSocket protocol version field to support forward/backward compatibility.

## What I learned

The highest-leverage decision was putting the simulation behind a clean,
event-draining interface: it made the server testable, kept the WebSocket layer
thin, and forced a clear message protocol. Server-authoritative design
simplifies security (validate intentions, compute outcomes) and removes an
entire class of bugs. Keeping the client as a pure renderer of snapshots plus a
thin input sampler made the rendering and network code far easier to reason
about, and the fixed-tick + snapshot-broadcast pattern is a reliable baseline
for real-time games.
