# Queue Cure 2026

🏆 Queue Cure '26 Hackathon Submission

⚡ 100% Real-Time Updates
🔄 Zero Polling
🚫 Zero Manual Refresh
🏥 Healthcare Queue Management System

Built using Flask, Flask-SocketIO, SQLite, Bootstrap 5, HTML, CSS and JavaScript.

---

## Why Queue Cure 2026?

According to the hackathon problem statement, many clinics still rely on paper-token systems, manual announcements, and disconnected communication between receptionists and patients.

Queue Cure 2026 solves this problem through real-time queue visibility powered by WebSockets.

### Benefits
- Eliminates manual queue announcements
- Reduces patient uncertainty and frustration
- Provides transparent wait-time estimation
- Synchronizes all screens instantly
- Improves clinic operational efficiency
- Creates a modern patient experience

---

## Why This Project Matters

Many clinics still rely on paper-token systems and manual announcements.

Queue Cure Clinic modernizes patient queue management by providing:
- Live queue visibility
- Real-time patient updates
- Smart wait-time estimation
- Receptionist productivity tools
- Operational analytics

The result is a smoother experience for both patients and clinic staff.

---

## Feature Highlights

✅ Real-Time WebSocket Synchronization
✅ Receptionist Dashboard
✅ Patient Waiting Room
✅ Analytics Dashboard
✅ Queue History
✅ Activity Logs
✅ Queue Reset
✅ Smart Wait-Time Estimation
✅ CSV Export
✅ Mobile Responsive Design
✅ Dark Mode
✅ Doctor Status Tracking
✅ Clinic Branding Support

---

## Hackathon Evaluation Alignment

| Criteria | Implementation |
|-----------|---------------|
| Live Queue Updates | Flask-SocketIO WebSockets |
| Real Wait Time Calculation | Patients Ahead × Consultation Time |
| Receptionist Usability | Dashboard + Validation + Search |
| Edge Cases | Reconnect, Queue Reset, Duplicate Prevention |

---

## Architecture

```text
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
Patient Waiting Room    Analytics Dashboard

Instant Updates Without Refresh
```

---

## Real-Time Innovation

Unlike traditional web applications that rely on manual refreshes or polling, Queue Cure 2026 uses WebSocket communication through Flask-SocketIO.

Every queue action instantly propagates to:
- Receptionist Dashboard
- Patient Waiting Room
- Analytics Dashboard

This creates a truly synchronized clinic experience.

---

## Project Impact

Queue Cure 2026 transforms traditional paper-token workflows into a modern real-time healthcare management experience.

### Expected Outcomes
- Faster patient servicing
- Reduced waiting uncertainty
- Better receptionist productivity
- Transparent queue visibility
- Improved patient satisfaction
- Real-time operational insights

---

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
