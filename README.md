# CYBER ARENA

**Capture. Attack. Defend. Dominate.**

A real-time, server-authoritative multiplayer strategy/action game for 2–4 players.
Players battle inside a cyber-themed arena to capture network nodes, collect data,
shoot opponents, and accumulate the highest score before the match timer ends.

- **Backend:** Python 3.13 · FastAPI · WebSockets · MongoDB (optional)
- **Frontend:** React 18 · TypeScript · HTML Canvas · Vite
- **Architecture:** server-authoritative game loop with room-based matchmaking

---

## Features

- Room-code lobby (create / join, 2–4 players, host starts the match)
- Live multiplayer with WebSocket synchronization at 20 ticks/second
- Capture network nodes (neutral → owned; contesting reverses progress)
- Combat: aim with mouse, shoot, take damage, die, respawn
- Power-ups: speed boost, shield, overcharge
- Score from kills and node ownership; win at time-up or score cap
- HUD (health, score, kills, leaderboard, match timer) and event notifications
- Results screen with rankings, stats, play-again / return-to-lobby
- Graceful disconnect handling with a reconnect window
- MongoDB persistence for players and match history (with in-memory fallback)

---

## Repository layout

```
cyber arena/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint
│   │   ├── api/routes.py        # REST: health, leaderboard, history
│   │   ├── websocket/           # WS endpoint + connection manager
│   │   ├── rooms/room.py        # Room + RoomManager (lobby/state machine)
│   │   ├── game/                # engine, models, map, geometry, constants
│   │   ├── services/            # persistence (MongoDB / in-memory)
│   │   ├── config/settings.py   # env-driven config
│   │   └── utils/
│   ├── tests/                   # pytest suite
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/          # Home, Lobby, Game, Results screens
│       ├── game/                # client engine, renderer, physics, constants
│       ├── hooks/               # useNetwork
│       ├── services/            # socket + network client
│       ├── types/
│       └── App.tsx              # screen state machine
├── .env.example
└── PROJECT_DECISIONS.md
```

---

## Run locally

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- (Optional) MongoDB — the game runs without it via in-memory persistence

### 1. Clone & configure

```bash
git clone <repo-url>
cd cyber\ arena
```

Backend environment:

```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env      # edit as needed; MONGO_URL optional
```

### 2. Start the backend

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify: open `http://localhost:8000/api/health` → `{"status":"ok"}`.

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api` and `/ws` to the
backend, so no extra CORS config is needed.

### 4. Play

1. Open two or more browser windows at `http://localhost:5173`.
2. Enter a display name in each window.
3. In one window choose **Create Room**; note the room code.
4. In the others choose **Join Room** and enter that code.
5. The host clicks **Start Match** when at least 2 players are present.
6. Move with **WASD / arrows**, aim with the mouse, hold **click** to shoot.

---

## Testing

Backend:

```bash
cd backend
python -m pytest -q
```

The suite covers room creation/join/disconnect, capture logic, combat damage,
score, and match state transitions.

Frontend type/build check:

```bash
cd frontend
npm run build
```

---

## Environment variables

See `.env.example`. Required keys are prefilled with local defaults; only
`MONGO_URL` is optional (empty → in-memory persistence).

| Variable      | Description                                        |
| ------------- | -------------------------------------------------- |
| `HOST`        | Backend bind host                                   |
| `PORT`        | Backend port (default 8000)                         |
| `CORS_ORIGINS`| Comma-separated allowed browser origins             |
| `MONGO_URL`   | MongoDB connection string (empty = in-memory)       |
| `MONGO_DB`    | Database name                                       |
| `DEBUG`       | Verbose logging                                     |

Never commit real credentials. Use `.env` files (git-ignored).

---

## Deployment

### Backend

Any ASGI host works. Example with `uvicorn`:

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

> Use **one worker**. The in-memory room/engine state lives per process; a
> multi-worker setup requires a shared pub/sub transport (out of scope for MVP).

Set `CORS_ORIGINS` to your frontend origin. For production WebSockets, put the
app behind a reverse proxy (nginx/Caddy) that forwards both `/api` (HTTP) and
`/ws` (upgrade) to the app.

### Frontend

```bash
cd frontend
npm install
npm run build
```

Serve the `dist/` directory with any static host (nginx, S3+CloudFront, etc.)
and configure it to proxy `/api` and `/ws` to the backend, or serve the backend
under the same origin.

---

## Known limitations

- Single-process room storage (works across browsers on one server; not for
  horizontal scaling without a shared pub/sub layer).
- No sound, no spectator mode, single map.
- Reconnect restores your slot but not a live mid-match state snapshot replay.

## Future improvements

- Multiple maps and a map selector
- Sound effects + ambient audio
- Spectator mode
- Global matchmaking and ranked leaderboards
- Horizontal scaling with Redis pub/sub for room state
- Client-side prediction for smoother local movement under high latency

See `PROJECT_DECISIONS.md` for architecture rationale and trade-offs.
