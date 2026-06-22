# Thought Process — Queue Cure 2026

## Problem

Clinics still use paper token systems where patients have no visibility into queue position, estimated wait time, or current serving token. Receptionists manually announce numbers, creating noise and inefficiency. There is no digital audit trail or analytics.

## Solution

A lightweight, real-time web application that:
1. Lets receptionists manage the queue digitally
2. Displays live status on a patient-facing screen
3. Calculates wait times dynamically from configurable consultation duration
4. Syncs all views instantly without page refresh

## Architecture Decisions

### Why Flask + Flask-SocketIO?
- Minimal setup for hackathon timeline
- Flask-SocketIO provides battle-tested WebSocket abstraction
- Single-process deployment works well on Render free tier
- Python ecosystem familiar to most developers

### Why SQLite?
- Zero configuration — database file created at runtime
- Sufficient for single-clinic deployment
- Render persistent disk mount preserves data across deploys
- Easy to export via CSV for reporting

### Why WebSockets (Not Polling)?
- Requirement: instant updates across all screens
- Polling adds latency, server load, and battery drain
- Socket.IO handles reconnection, fallbacks, and room broadcasting
- One `queue_updated` event replaces multiple REST round-trips

### Why REST + WebSockets Hybrid?
- REST for mutations (POST/PUT/DELETE) with validation and error responses
- WebSockets for broadcasting state to all connected clients
- Pattern: API action → DB update → socket broadcast → all UIs re-render

## Concurrency Considerations

- SQLite handles concurrent reads well; writes are serialized
- Token number generation uses `MAX(token_number) + 1` within a transaction
- Duplicate name check runs in same transaction as insert
- For high-traffic clinics, migrate to PostgreSQL with row-level locking

## Real-Time Strategy

Every state-changing operation calls `broadcast_queue_update()` which:
1. Rebuilds full queue state from DB
2. Emits `queue_updated` to all clients
3. Emits `analytics_updated` with recalculated metrics

Clients maintain no local state authority — server is source of truth. On reconnect, client requests fresh state via `request_state`.

## Wait Time Formula

```
Estimated Wait (minutes) = Patients Waiting × Average Consultation Time
```

- Average consultation time stored in `settings` table (not hardcoded)
- Recalculated on every queue change and settings update
- Displayed on both receptionist dashboard and patient waiting room

## Edge Cases

| Scenario | Handling |
|----------|----------|
| Empty queue + Call Next | HTTP 400, toast error message |
| Duplicate patient name | HTTP 409, inline validation error |
| Empty patient name | HTTP 400, form validation |
| Invalid consultation time | HTTP 400, range 1–120 minutes |
| Queue reset | Confirmation modal, marks all active as removed |
| Remove patient | Confirmation modal with patient name |
| Browser disconnect | Socket.IO auto-reconnect + state refresh |
| Multiple receptionist tabs | All receive same broadcasts |
| Simultaneous patient adds | SQLite serializes; tokens stay sequential |

## Scalability Path

**Current (single clinic):**
- 1 Gunicorn worker with Eventlet
- SQLite on persistent disk
- Handles dozens of concurrent WebSocket connections

**Future (multi-clinic):**
- PostgreSQL with connection pooling
- Redis message queue for SocketIO multi-worker (`socketio.init_app(app, message_queue='redis://...')`)
- Separate rooms per clinic (`join_room(clinic_id)`)
- Horizontal scaling on Render/Railway/Fly.io

## Security Considerations

- No authentication in MVP (suitable for internal clinic network)
- Production should add session auth for dashboard
- Patient display is read-only via WebSocket (no mutation endpoints exposed in UI)
- SECRET_KEY from environment variable on Render
- Input validation on all API endpoints
- SQL parameterized queries (no injection)

## UI/UX Decisions

- Bootstrap 5 for rapid, professional styling
- Dark mode via `data-bs-theme` attribute + localStorage persistence
- Gradient stat cards for visual hierarchy
- Patient display optimized for wall-mounted tablet/TV
- Toast notifications for action feedback (no alert boxes)
- Loading spinners on async buttons
- Confirmation modals for destructive actions

## Future Improvements

1. **Authentication** — Login for receptionist, public read-only patient view
2. **Multi-room** — Separate queues per doctor/specialty
3. **Notifications** — SMS when 2 patients ahead
4. **Appointments** — Pre-register patients with scheduled times
5. **PWA** — Installable mobile app for reception
6. **Analytics history** — Charts over days/weeks/months
7. **Internationalization** — Multi-language patient display
