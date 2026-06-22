# Queue Cure 2026

**Modern real-time clinic queue management system** — replacing paper tokens with live queue visibility powered by WebSockets.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![Socket.IO](https://img.shields.io/badge/Socket.IO-5.3-orange)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple)

---

## Overview

Queue Cure 2026 is a full-stack clinic queue management application designed for hackathon and production deployment. Receptionists manage the patient queue from a dashboard while patients view live status on a waiting room display — all synchronized instantly via Flask-SocketIO WebSockets with **zero page refreshes** and **no polling**.

## Why Queue Cure 2026?

According to the hackathon problem statement, many clinics still rely on paper-token systems, manual announcements, and disconnected communication between receptionists and patients.

Queue Cure 2026 solves this problem through real-time queue visibility powered by WebSockets.

Benefits:
- Eliminates manual queue announcements
- Reduces patient uncertainty and frustration
- Provides transparent wait-time estimation
- Synchronizes all screens instantly
- Improves clinic operational efficiency
- Creates a modern patient experience

## Problem Statement

Traditional clinic queues rely on paper tokens and manual announcements, leading to:
- Patients unsure of their position or wait time
- Receptionists repeating status updates verbally
- No visibility into daily throughput or analytics
- Disconnected experience between staff and waiting patients

## Features

| Feature | Description |
|---------|-------------|
| **Real-Time Sync** | All screens update instantly via WebSocket events |
| **Auto Token Numbers** | Sequential tokens assigned automatically |
| **Wait Time Estimates** | `Patients Ahead × Avg Consultation Time` |
| **Receptionist Dashboard** | Add, call, remove, reset queue; settings; activity log |
| **Patient Waiting Room** | Large token display, mobile-first, live status |
| **Analytics Dashboard** | Served today, completion rate, live metrics |
| **Dark Mode** | Toggle across all admin screens |
| **CSV Export** | Download full patient queue history |
| **Edge Case Handling** | Empty queue, duplicates, reconnect, validation |

## Hackathon Evaluation Mapping

| Evaluation Criteria | How Queue Cure Solves It |
|---------------------|--------------------------|
| Live Queue Updates (40%) | Flask-SocketIO broadcasts updates instantly across all connected screens |
| Real Wait-Time Calculation (25%) | Wait time = Patients Ahead × Average Consultation Time |
| Receptionist Usability (20%) | One-click patient management, validation, search, confirmations, activity logs |
| Edge Cases & Concurrency (15%) | Reconnect handling, queue reset confirmation, duplicate prevention, multi-tab synchronization |

## Architecture

Receptionist Dashboard
         │
         │ Add / Call / Remove Patient
         ▼
Flask + Socket.IO Server
         │
         ▼
SQLite Database
         │
         ▼
Broadcast Real-Time Events
         │
  ┌──────┴─────────┐
  ▼                ▼
Patient Room   Analytics Dashboard

Instant Updates Without Refresh

**Stack:** Python Flask · Flask-SocketIO · SQLite · HTML/CSS/JS · Bootstrap 5 · Socket.IO Client · Gunicorn + Eventlet (Render)

## Real-Time Innovation

Unlike traditional web applications that rely on manual refreshes or polling, Queue Cure 2026 uses WebSocket communication through Flask-SocketIO.

Every queue action instantly propagates to:
- Receptionist Dashboard
- Patient Waiting Room
- Analytics Dashboard

This creates a truly synchronized clinic experience.

## Screenshots

> Add screenshots after running locally:
> - Landing page (`/`)
> - Receptionist Dashboard (`/dashboard`)
> - Patient Waiting Room (`/patient`)
> - Analytics Dashboard (`/analytics`)

## Database Design

### `patients`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment ID |
| token_number | INTEGER | Display token number |
| patient_name | TEXT | Patient name |
| status | TEXT | waiting, called, served, removed |
| created_at | TEXT (ISO) | When added to queue |
| served_at | TEXT (ISO) | When called/served/removed |

### `settings`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Always 1 (singleton) |
| average_consultation_time | INTEGER | Minutes (1–120) |
| doctor_status | TEXT | available / busy |
| clinic_name | TEXT | Branding name |

### `activity_logs`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| action | TEXT | Human-readable log entry |
| timestamp | TEXT (ISO) | When action occurred |

## Socket Events

| Event | Direction | Trigger |
|-------|-----------|---------|
| `queue_updated` | Server → Client | Any queue state change |
| `patient_added` | Server → Client | New patient added |
| `patient_removed` | Server → Client | Patient removed |
| `patient_called` | Server → Client | Patient called |
| `settings_updated` | Server → Client | Settings changed |
| `queue_reset` | Server → Client | Queue cleared |
| `analytics_updated` | Server → Client | Metrics recalculated |
| `request_state` | Client → Server | Request full state (reconnect) |

See [docs/socket_diagram.md](docs/socket_diagram.md) for the complete flow diagram.

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Landing page |
| GET | `/dashboard` | Receptionist dashboard |
| GET | `/patient` | Patient waiting room |
| GET | `/analytics` | Analytics dashboard |
| GET | `/api/patients` | Full queue state (JSON) |
| POST | `/api/patients` | Add patient |
| POST | `/api/patients/call-next` | Call next in queue |
| POST | `/api/patients/:id/call` | Call specific patient |
| DELETE | `/api/patients/:id` | Remove patient |
| POST | `/api/patients/:id/complete` | Mark consultation done |
| GET/PUT | `/api/settings` | Read/update settings |
| POST | `/api/queue/reset` | Reset active queue |
| GET | `/api/analytics` | Analytics metrics |
| GET | `/api/export` | CSV export |

Full API docs: [docs/api_documentation.md](docs/api_documentation.md)

## Installation

### Prerequisites
- Python 3.11+
- pip

### Local Setup

```bash
cd queue-cure
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-dev.txt  # optional, for tests

python app.py
```

Open:
- http://localhost:5000 — Landing
- http://localhost:5000/dashboard — Receptionist
- http://localhost:5000/patient — Waiting Room
- http://localhost:5000/analytics — Analytics

### Run Tests

```bash
pytest tests/ -v
```

## Deployment (Render)

1. Push the `queue-cure/` directory to GitHub
2. Create a new **Web Service** on [Render](https://render.com)
3. Connect your repo; Render detects `render.yaml` automatically
4. Deploy — no code changes required

The `render.yaml` configures:
- Gunicorn with Eventlet worker (required for WebSockets)
- Persistent disk at `/var/data` for SQLite
- Auto-generated `SECRET_KEY`

See [docs/deployment_guide.md](docs/deployment_guide.md) for details.

## Edge Cases Handled

- **Empty queue** — Call Next shows error toast; displays "Queue is empty"
- **Duplicate names** — Rejected if patient already waiting/called (409)
- **Invalid consultation time** — Validated 1–120 minutes
- **Queue reset** — Confirmation modal before clearing
- **Remove patient** — Confirmation modal required
- **Browser reconnect** — Auto-reconnect + `request_state` on connect
- **Multiple tabs** — All tabs receive same WebSocket broadcasts
- **Simultaneous additions** — SQLite serializes writes; unique token increment

## Project Impact

Queue Cure 2026 transforms traditional paper-token workflows into a modern real-time healthcare management experience.

Expected Outcomes:
- Faster patient servicing
- Reduced waiting uncertainty
- Better receptionist productivity
- Transparent queue visibility
- Improved patient satisfaction
- Real-time operational insights

## Future Improvements

- Multi-doctor / multi-room support
- SMS/email notifications when patient's turn approaches
- Appointment scheduling integration
- PostgreSQL for multi-instance deployment
- Role-based authentication (receptionist vs admin)
- QR code check-in for patients
- Historical analytics with date range filters
- PWA support for mobile receptionist app

## Hackathon Submission Deliverables

✅ Working Prototype
✅ GitHub Repository
✅ README Documentation
✅ Socket Event Diagram
✅ Thought Process Document
✅ Analytics Dashboard
✅ Real-Time WebSocket Synchronization
✅ Deployment Ready on Render
✅ Mobile Responsive Design

## Project Structure

```
queue-cure/
├── app.py                  # Flask app + SocketIO + API
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Test dependencies
├── render.yaml             # Render deployment config
├── README.md
├── .gitignore
├── templates/
│   ├── landing.html
│   ├── dashboard.html
│   ├── patient.html
│   └── analytics.html
├── static/
│   ├── style.css
│   └── script.js
├── docs/
│   ├── socket_diagram.md
│   ├── thought_process.md
│   ├── api_documentation.md
│   ├── deployment_guide.md
│   └── test_cases.md
└── tests/
    ├── conftest.py
    ├── test_api.py
    └── test_socketio.py
```

## License

MIT — Built for hackathon submission, Queue Cure 2026.
