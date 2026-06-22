# Socket.IO Event Flow Diagram

## Connection Lifecycle

```mermaid
sequenceDiagram
    participant C as Client (Browser)
    participant S as Flask-SocketIO Server
    participant DB as SQLite

    C->>S: connect (WebSocket)
    S->>DB: build_queue_state()
    S->>C: queue_updated (full state)
    S->>C: analytics_updated (metrics)

    Note over C,S: Auto-reconnect on disconnect
    C->>S: reconnect
    C->>S: request_state
    S->>DB: build_queue_state()
    S->>C: queue_updated
    S->>C: analytics_updated
```

## Patient Added Flow

```mermaid
sequenceDiagram
    participant R as Receptionist Dashboard
    participant API as REST API
    participant S as SocketIO Server
    participant DB as SQLite
    participant P as Patient Display
    participant A as Analytics Page

    R->>API: POST /api/patients {patient_name}
    API->>DB: INSERT patient, log activity
    API->>S: emit patient_added
    API->>S: broadcast queue_updated
    API->>S: broadcast analytics_updated
    S->>R: patient_added
    S->>P: queue_updated
    S->>A: queue_updated + analytics_updated
    API->>R: 201 Created
```

## Call Next Patient Flow

```mermaid
sequenceDiagram
    participant R as Receptionist
    participant API as REST API
    participant S as SocketIO
    participant All as All Connected Clients

    R->>API: POST /api/patients/call-next
    alt Queue Empty
        API->>R: 400 Error
    else Has Waiting Patient
        API->>API: Mark previous called → served
        API->>API: Mark next waiting → called
        API->>API: Set doctor_status = busy
        API->>S: emit patient_called
        API->>S: broadcast queue_updated
        S->>All: patient_called + queue_updated
        API->>R: 200 OK
    end
```

## Settings Updated Flow

```mermaid
sequenceDiagram
    participant R as Receptionist
    participant API as REST API
    participant S as SocketIO
    participant All as All Clients

    R->>API: PUT /api/settings {average_consultation_time: 15}
    API->>API: Validate (1-120 min)
    API->>S: emit settings_updated
    API->>S: broadcast queue_updated
    Note over All: Wait times recalculated<br/>Patients Ahead × New Avg Time
    S->>All: settings_updated + queue_updated
```

## Queue Reset Flow

```mermaid
sequenceDiagram
    participant R as Receptionist
    participant M as Confirm Modal
    participant API as REST API
    participant S as SocketIO
    participant All as All Clients

    R->>M: Click Reset Queue
    M->>R: Confirm?
    R->>API: POST /api/queue/reset
    API->>API: Mark all waiting/called → removed
    API->>API: Set doctor_status = available
    API->>S: emit queue_reset
    API->>S: broadcast queue_updated
    S->>All: queue_reset + queue_updated
```

## Event Summary Table

| Event | Emitter | Payload | Subscribers |
|-------|---------|---------|-------------|
| `connect` | Client | — | Server responds with state |
| `request_state` | Client | — | Server sends full state |
| `queue_updated` | Server | Full queue state object | All pages |
| `patient_added` | Server | Patient object | Dashboard (toast) |
| `patient_removed` | Server | Patient object | Dashboard (toast) |
| `patient_called` | Server | Patient object | All pages (flash token) |
| `settings_updated` | Server | Settings object | Dashboard, Patient |
| `queue_reset` | Server | `{message}` | Dashboard (toast) |
| `analytics_updated` | Server | Analytics object | Analytics, Dashboard stats |

## State Object Structure (`queue_updated`)

```json
{
  "settings": {
    "average_consultation_time": 10,
    "doctor_status": "available",
    "clinic_name": "Queue Cure Clinic"
  },
  "waiting": [{ "id": 1, "token_number": 1, "patient_name": "...", "status": "waiting", ... }],
  "current": { "id": 2, "token_number": 2, "status": "called", ... },
  "history": [...],
  "activity": [{ "id": 1, "action": "...", "timestamp": "..." }],
  "analytics": { "patients_served_today": 5, "total_today": 8, ... },
  "waiting_count": 3,
  "estimated_wait_minutes": 30
}
```

## Client Reconnection Strategy

1. Socket.IO client configured with `reconnection: true`, infinite attempts
2. On `connect` event → emit `request_state`
3. Connection badge shows "Live" (green) or "Reconnecting..." (red)
4. No HTTP polling — WebSocket transport preferred, polling fallback only for handshake
