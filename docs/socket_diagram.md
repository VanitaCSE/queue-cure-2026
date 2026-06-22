# Socket Event Diagram

## Real-Time Communication Flow

```text
Receptionist Dashboard
         │
         │ Add Patient
         │ Call Next
         │ Remove Patient
         │ Update Settings
         │ Reset Queue
         ▼
Flask-SocketIO Server
         │
         ▼
SQLite Database Updated
         │
         ▼
Broadcast Socket Event
         │
  ┌──────┼─────────────┐
  ▼      ▼             ▼
Dashboard   Waiting Room   Analytics

All connected screens update instantly
without refresh or polling.
```

## Socket Events

| Event | Trigger | Purpose |
|---------|---------|---------|
| patient_added | New patient added | Update all screens |
| patient_removed | Patient removed | Refresh queue |
| patient_called | Next token called | Update current token |
| queue_updated | Queue state changes | Synchronize clients |
| settings_updated | Consultation time changed | Recalculate wait times |
| queue_reset | Queue cleared | Reset all screens |
| analytics_updated | Analytics recalculated | Refresh metrics |
| request_state | Client reconnects | Recover latest state |

## Example Flow

```text
Receptionist clicks "Add Patient"
            │
            ▼
Database stores patient
            │
            ▼
Socket Event: patient_added
            │
            ▼
Server broadcasts update
            │
  ┌──────────┴──────────┐
  ▼                     ▼
Waiting Room      Analytics Page
Updated           Updated
Instantly         Instantly
```

## Why WebSockets?

Traditional polling:
Client → Request → Server → Response → Repeat

Problems:
- Delayed updates
- Higher server load
- Poor user experience

Queue Cure 2026 uses WebSockets:
Server ↔ Client

Benefits:
- Instant updates
- Lower bandwidth
- Better scalability
- Improved patient experience
