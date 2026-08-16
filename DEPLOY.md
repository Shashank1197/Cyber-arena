# Deploying Cyber Arena

Cyber Arena is two services: a **FastAPI backend** (game simulation over WebSockets) and a **React frontend** (served by nginx, which reverse-proxies `/api` and `/ws` to the backend). Anyone with your deployed URL can open the game, create/join a room by code, and play together in real time.

> **Important — one worker.** Room and match state live in the backend's process memory. Run the backend with a single worker; horizontal scaling needs a shared pub/sub layer (not implemented).

> **Important — one origin.** The frontend connects the WebSocket to `window.location.host` (`frontend/src/services/socket.ts`), so the URL that serves the page must also route `/api` and `/ws`. The provided nginx proxy handles this automatically.

---

## Option A — VPS with Docker (recommended, zero platform lock-in)

Requires Docker + Docker Compose on the host.

```bash
git clone <your-repo-url>
cd cyber\ arena

# Optional: set the public origin and a MongoDB URL (leave Mongo empty for
# in-memory persistence). Create a .env at the repo root.
echo "CORS_ORIGINS=http://YOUR_IP:8080" > .env

docker compose up -d --build
```

Open `http://YOUR_IP:8080`.

### Env vars (`docker-compose.yml` / `.env`)
| Variable | Default | Purpose |
|----------|---------|---------|
| `PORT` | `8080` | Host port the game is served on |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed browser origin (set to your public URL) |
| `MONGO_URL` | empty | MongoDB URI; empty = in-memory persistence |
| `MONGO_DB` | `cyber_arena` | Database name |
| `BACKEND_HOST` | `backend` | Backend hostname nginx proxies to (compose DNS) |
| `BACKEND_PORT` | `8000` | Backend port |

### HTTPS (so browsers use `wss://`)
Terminate TLS in front of the container. The easiest path on a domain:
```bash
sudo certbot --nginx   # if nginx is the host proxy, or use any reverse proxy
```
The frontend already switches to `wss://` automatically when the page is served over HTTPS (`socket.ts:120-123`).

---

## Option B — Render (managed, no server admin)

This repo includes `render.yaml` (a Render Blueprint). After you've connected your GitHub repo to Render:

1. Create a **Blueprint** from `render.yaml`.
2. Set the secret env vars Render asks for (`CORS_ORIGINS`, `MONGO_URL`, `BACKEND_HOST`).
3. Deploy both services.

**One-time wiring step (single origin):**
- After the backend deploys, copy its URL, e.g. `https://cyber-arena-backend.onrender.com`.
- Set the frontend service env var `BACKEND_HOST` to that URL (strip the `https://`; the frontend nginx proxies to it) — or set `BACKEND_HOST` to the full origin if using the template's hostname logic.
- Redeploy the frontend.

> On Render, the backend URL is `https://<name>.onrender.com`. Set the frontend `BACKEND_HOST` to `<name>.onrender.com` and `BACKEND_PORT` to `443` (or `80`). The frontend nginx will proxy `/api` and `/ws` to it.

---

## Option C — Fly.io / Railway

Both platforms can build either `Dockerfile` (backend) or the frontend Docker image. Use the same single-origin rule: either run both behind one nginx (Option A image) or point the frontend nginx at the backend service via `BACKEND_HOST`.

---

## Verifying a deployment

```bash
# Health endpoint
curl http://YOUR_URL/api/health        # {"status":"ok","app":"Cyber Arena","mongo":...}

# The WebSocket handshake should not be rejected:
# open two browsers at YOUR_URL, create a room in one, join with the code in the other.
```

## Updating after a code change
```bash
git push origin main
# on the VPS:
git pull
docker compose up -d --build
```
Render/Fly/Railway redeploy automatically on push.

---

## Option D — Vercel (frontend) + separate backend host

Vercel serves static sites and **cannot run the Python backend or proxy persistent WebSockets**. Use it for the frontend only, and run the backend elsewhere (Railway, Render, Fly, or a VPS).

1. **Deploy the backend first** on any Python host (see Option A/B/C), producing a public URL, e.g. `https://cyber-backend.onrender.com`.
2. **Frontend on Vercel:**
   - Connect your GitHub repo to Vercel, root directory `frontend`, build `npm run build`, output `dist`.
   - Set the build env var `VITE_API_URL=https://your-backend.onrender.com` (no trailing slash). This makes `buildWsUrl()` (`frontend/src/services/socket.ts`) connect to the backend over `wss://`.
   - Add a `vercel.json` (included) so deep links rewrite to `index.html`.
3. **Backend CORS:** set the backend's `CORS_ORIGINS` to your Vercel URL, e.g. `https://your-app.vercel.app`.

The included `socket.ts` change means the same build works on Vercel (`VITE_API_URL` set) or same-origin docker-compose (`VITE_API_URL` empty).

---

## Files that make this work
- `backend/Dockerfile` — backend image (uvicorn, 1 worker)
- `frontend/Dockerfile` — multi-stage build (npm ci → vite build → nginx)
- `frontend/nginx.conf.template` — SPA + `/api` + `/ws` proxy, host configurable at runtime
- `frontend/entrypoint.sh` — substitutes `BACKEND_HOST`/`BACKEND_PORT` into the nginx template
- `docker-compose.yml` — single-command VPS deploy
- `render.yaml` — Render Blueprint
