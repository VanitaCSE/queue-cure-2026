# Deployment Guide — Queue Cure 2026

## Render Deployment (Recommended)

Queue Cure 2026 includes a `render.yaml` Blueprint for one-click deployment.

### Prerequisites

1. GitHub account with the repository pushed
2. [Render](https://render.com) account (free tier works)

### Steps

#### 1. Push to GitHub

```bash
cd queue-cure
git init
git add .
git commit -m "Initial commit: Queue Cure 2026"
git remote add origin https://github.com/YOUR_USERNAME/queue-cure-2026.git
git push -u origin main
```

#### 2. Deploy on Render

**Option A — Blueprint (render.yaml):**
1. Go to Render Dashboard → **New** → **Blueprint**
2. Connect your GitHub repo
3. Render reads `render.yaml` and creates the web service
4. Click **Apply**

**Option B — Manual Web Service:**
1. **New** → **Web Service**
2. Connect repo, set root directory to `queue-cure` if monorepo
3. Configure:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app`
4. Add environment variables:
   - `PYTHON_VERSION` = `3.11.9`
   - `SECRET_KEY` = (generate random string)
   - `DATABASE_PATH` = `/var/data/database.db`
5. Add **Persistent Disk:**
   - Mount path: `/var/data`
   - Size: 1 GB

#### 3. Verify Deployment

- Visit your Render URL (e.g., `https://queue-cure-2026.onrender.com`)
- Open `/dashboard` and `/patient` in two tabs
- Add a patient — both tabs should update instantly

### render.yaml Reference

```yaml
services:
  - type: web
    name: queue-cure-2026
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
    envVars:
      - key: PYTHON_VERSION
        value: "3.11.9"
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_PATH
        value: /var/data/database.db
    disk:
      name: queue-cure-data
      mountPath: /var/data
      sizeGB: 1
```

### Why Eventlet + 1 Worker?

Flask-SocketIO requires an async worker for WebSocket support. Gunicorn's default sync workers do not support WebSockets.

- `--worker-class eventlet` enables async I/O
- `-w 1` single worker avoids multi-process SocketIO state issues (without Redis)
- For scaling beyond 1 worker, add Redis as message queue

---

## Local Production Simulation

Test with Gunicorn locally before deploying:

```bash
pip install -r requirements.txt
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Production | dev key | Flask session secret |
| `DATABASE_PATH` | No | `./database.db` | SQLite file path |
| `PORT` | Render | 5000 | Server port |
| `FLASK_DEBUG` | No | off | Enable debug mode |

---

## Persistent Storage

SQLite database is stored at `DATABASE_PATH`. On Render:
- Without persistent disk: data lost on each deploy
- With persistent disk (`/var/data`): data survives deploys and restarts

The `render.yaml` includes a 1 GB persistent disk mounted at `/var/data`.

---

## Troubleshooting

### WebSockets not connecting
- Ensure start command uses `--worker-class eventlet`
- Check browser console for connection errors
- Render free tier may spin down after inactivity — first request wakes the service

### Database errors on deploy
- Verify `DATABASE_PATH` points to persistent disk mount
- Ensure disk is attached in Render service settings

### 502 Bad Gateway
- Check Render logs for Python import errors
- Verify all dependencies in `requirements.txt`
- Confirm Python version matches (3.11)

### Static files not loading
- Flask serves static files automatically from `static/`
- CDN resources (Bootstrap, Socket.IO) require internet access

---

## Alternative Platforms

### Railway
```bash
# Procfile
web: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
```

### Fly.io
Add `fly.toml` with internal port 5000 and mount a volume for SQLite.

### Docker (optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV DATABASE_PATH=/data/database.db
CMD gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
```

---

## Post-Deployment Checklist

- [ ] Landing page loads
- [ ] Dashboard adds patients
- [ ] Patient display updates in real-time
- [ ] Call Next works
- [ ] Settings save and propagate
- [ ] Queue reset works with confirmation
- [ ] CSV export downloads
- [ ] Analytics shows live metrics
- [ ] WebSocket reconnects after tab sleep
