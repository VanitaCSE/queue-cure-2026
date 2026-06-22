# Socket Event Diagram

```text
Receptionist Dashboard
         │
         ▼
Patient Added / Called / Removed
         │
         ▼
Flask Socket.IO Server
         │
         ▼
SQLite Database Updated
         │
         ▼
Broadcast Event
         │
  ┌──────┴─────────┐
  ▼                ▼
Patient Waiting Room   Analytics Dashboard

All connected clients update instantly.
```

## Events Used
- patient_added
- patient_removed
- patient_called
- queue_updated
- settings_updated
- queue_reset
- analytics_updated
