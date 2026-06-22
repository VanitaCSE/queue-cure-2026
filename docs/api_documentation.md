# API Documentation — Queue Cure 2026

Base URL: `http://localhost:5000` (local) or your Render deployment URL.

All JSON endpoints return `Content-Type: application/json` unless noted.

---

## Pages

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Landing page (HTML) |
| `/dashboard` | GET | Receptionist dashboard (HTML) |
| `/patient` | GET | Patient waiting room (HTML) |
| `/analytics` | GET | Analytics dashboard (HTML) |

---

## Patients

### GET `/api/patients`

Returns full queue state.

**Response 200:**
```json
{
  "settings": {
    "average_consultation_time": 10,
    "doctor_status": "available",
    "clinic_name": "Queue Cure Clinic"
  },
  "waiting": [
    {
      "id": 1,
      "token_number": 1,
      "patient_name": "John Doe",
      "status": "waiting",
      "created_at": "2026-06-20T10:00:00+00:00",
      "served_at": null
    }
  ],
  "current": null,
  "history": [],
  "activity": [],
  "analytics": { ... },
  "waiting_count": 1,
  "estimated_wait_minutes": 10
}
```

---

### POST `/api/patients`

Add a patient to the queue.

**Request Body:**
```json
{
  "patient_name": "John Doe"
}
```

**Response 201:**
```json
{
  "patient": {
    "id": 1,
    "token_number": 1,
    "patient_name": "John Doe",
    "status": "waiting",
    "created_at": "2026-06-20T10:00:00+00:00",
    "served_at": null
  }
}
```

**Errors:**
| Status | Condition |
|--------|-----------|
| 400 | Empty or missing name |
| 409 | Duplicate name already in queue (waiting/called) |

**Socket Events Emitted:** `patient_added`, `queue_updated`, `analytics_updated`

---

### POST `/api/patients/call-next`

Call the next waiting patient (lowest token number).

**Response 200:**
```json
{
  "patient": {
    "id": 1,
    "token_number": 1,
    "patient_name": "John Doe",
    "status": "called",
    "served_at": "2026-06-20T10:05:00+00:00"
  }
}
```

**Errors:**
| Status | Condition |
|--------|-----------|
| 400 | Queue is empty |

**Side Effects:**
- Previous `called` patient marked `served`
- Doctor status set to `busy`

**Socket Events:** `patient_called`, `queue_updated`, `analytics_updated`

---

### POST `/api/patients/:id/call`

Call a specific waiting patient by ID.

**Response 200:** Same as call-next.

**Errors:**
| Status | Condition |
|--------|-----------|
| 404 | Patient not found |
| 400 | Patient not in waiting status |

---

### DELETE `/api/patients/:id`

Remove a patient from the active queue.

**Response 200:**
```json
{
  "patient": {
    "id": 1,
    "status": "removed",
    ...
  }
}
```

**Errors:**
| Status | Condition |
|--------|-----------|
| 404 | Patient not found |
| 400 | Patient not removable (already served) |

**Socket Events:** `patient_removed`, `queue_updated`, `analytics_updated`

---

### POST `/api/patients/:id/complete`

Mark the currently called patient's consultation as complete.

**Response 200:** Patient with `status: "served"`

**Errors:**
| Status | Condition |
|--------|-----------|
| 404 | Patient not found |
| 400 | Patient not currently called |

**Side Effects:** Doctor status set to `available`

---

## Settings

### GET `/api/settings`

**Response 200:**
```json
{
  "average_consultation_time": 10,
  "doctor_status": "available",
  "clinic_name": "Queue Cure Clinic"
}
```

---

### PUT `/api/settings`

Update one or more settings.

**Request Body (partial update supported):**
```json
{
  "average_consultation_time": 15,
  "doctor_status": "busy",
  "clinic_name": "City Health Clinic"
}
```

**Validation:**
- `average_consultation_time`: integer, 1–120
- `doctor_status`: `"available"` or `"busy"`
- `clinic_name`: non-empty string, max 100 chars

**Errors:**
| Status | Condition |
|--------|-----------|
| 400 | Invalid values or empty body |

**Socket Events:** `settings_updated`, `queue_updated`, `analytics_updated`

---

## Queue

### POST `/api/queue/reset`

Clear all waiting and called patients (marks as removed).

**Response 200:**
```json
{
  "message": "Queue reset successfully.",
  "cleared": 5
}
```

**Socket Events:** `queue_reset`, `queue_updated`, `analytics_updated`

---

## Analytics

### GET `/api/analytics`

**Response 200:**
```json
{
  "patients_served_today": 12,
  "total_today": 18,
  "removed_today": 2,
  "waiting_count": 4,
  "average_consultation_time": 10,
  "estimated_wait_minutes": 40,
  "completion_rate": 66.7,
  "current_token": 15,
  "current_patient": "Jane Smith",
  "doctor_status": "busy"
}
```

**Socket Event:** `analytics_updated` (broadcast on state changes)

---

## Export

### GET `/api/export`

Download all patients as CSV.

**Response 200:** `Content-Type: text/csv`

```csv
Token,Patient Name,Status,Created At,Served At
1,John Doe,waiting,2026-06-20T10:00:00+00:00,
```

---

## WebSocket Events

Connect to `/socket.io/` using Socket.IO client v4.

### Client → Server

| Event | Payload | Description |
|-------|---------|-------------|
| `request_state` | none | Request full queue state (used on reconnect) |

### Server → Client

| Event | Payload | Description |
|-------|---------|-------------|
| `queue_updated` | Full state object | Complete queue snapshot |
| `patient_added` | Patient object | New patient notification |
| `patient_removed` | Patient object | Removal notification |
| `patient_called` | Patient object | Call notification |
| `settings_updated` | Settings object | Settings changed |
| `queue_reset` | `{message}` | Queue was reset |
| `analytics_updated` | Analytics object | Metrics updated |

On `connect`, server automatically sends `queue_updated` and `analytics_updated`.
