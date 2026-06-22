# Test Cases — Queue Cure 2026

## Manual Test Checklist

### Landing Page (`/`)
- [ ] Page loads with branding and hero section
- [ ] Navigation links work (Dashboard, Waiting Room, Analytics)
- [ ] Responsive on mobile viewport

### Receptionist Dashboard (`/dashboard`)
- [ ] Page loads without refresh
- [ ] Connection badge shows "Live" when connected
- [ ] Current time updates every second
- [ ] Dark mode toggle persists after reload

#### Add Patient
- [ ] Submit empty name → validation error shown
- [ ] Submit valid name → patient appears in waiting table
- [ ] Token auto-increments (#001, #002, ...)
- [ ] Duplicate name (case-insensitive) → error toast
- [ ] Toast notification on successful add
- [ ] Patient display updates without refresh

#### Call Next
- [ ] Click Call Next with patients waiting → current token updates
- [ ] Click Call Next on empty queue → error toast
- [ ] Doctor status changes to Busy
- [ ] Complete button enables for called patient
- [ ] Complete marks patient served, doctor Available

#### Remove Patient
- [ ] Click remove → confirmation modal appears
- [ ] Cancel → no change
- [ ] Confirm → patient removed, toast shown

#### Settings
- [ ] Change avg consultation time → save → wait times update everywhere
- [ ] Invalid time (0, 200) → error toast
- [ ] Change clinic name → updates sidebar and patient display
- [ ] Change doctor status → badge updates

#### Queue Reset
- [ ] Click Reset → confirmation modal
- [ ] Confirm → all waiting/called cleared
- [ ] Activity log records reset

#### Search
- [ ] Type in search box → filters waiting table

#### Other
- [ ] CSV export downloads file
- [ ] Activity log shows recent actions
- [ ] Queue history shows called/served/removed

### Patient Waiting Room (`/patient`)
- [ ] Large token display shows current called patient
- [ ] Waiting count updates live
- [ ] Estimated wait = waiting × avg consultation time
- [ ] Up Next grid shows upcoming patients
- [ ] Mobile layout readable
- [ ] Dark mode toggle works
- [ ] No page refresh needed for any update

### Analytics Dashboard (`/analytics`)
- [ ] Stats cards show live metrics
- [ ] Patients served today updates on complete
- [ ] Completion rate calculates correctly
- [ ] Export CSV link works

### WebSocket / Reconnect
- [ ] Open dashboard + patient in two tabs → both sync
- [ ] Disable network briefly → badge shows Reconnecting
- [ ] Re-enable network → auto-reconnect, state refreshes
- [ ] No HTTP polling in Network tab (WebSocket only)

---

## Automated Tests

Run with:
```bash
cd queue-cure
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ -v
```

### test_api.py — Unit Tests

| Test | Description |
|------|-------------|
| `TestPages::*` | All HTML pages return 200 |
| `TestPatientsAPI::test_add_patient_success` | POST creates patient with token 1 |
| `TestPatientsAPI::test_add_patient_empty_name` | Empty name returns 400 |
| `TestPatientsAPI::test_add_patient_duplicate_name` | Duplicate returns 409 |
| `TestPatientsAPI::test_auto_increment_token` | Tokens increment 1, 2, 3 |
| `TestPatientsAPI::test_call_next_success` | Call next marks patient called |
| `TestPatientsAPI::test_call_next_empty_queue` | Empty queue returns 400 |
| `TestPatientsAPI::test_remove_patient` | DELETE marks removed |
| `TestPatientsAPI::test_remove_nonexistent_patient` | 404 for invalid ID |
| `TestSettingsAPI::test_get_settings` | GET returns settings |
| `TestSettingsAPI::test_update_consultation_time` | PUT updates avg time |
| `TestSettingsAPI::test_invalid_consultation_time` | 0 and 200 return 400 |
| `TestQueueReset::test_reset_queue` | Reset clears waiting |
| `TestAnalytics::test_analytics_endpoint` | Analytics JSON structure |
| `TestExport::test_csv_export` | CSV contains patient data |

### test_socketio.py — Integration Tests

| Test | Description |
|------|-------------|
| `test_connect_receives_state` | Connect emits queue_updated |
| `test_patient_added_broadcasts` | Add triggers socket events |
| `test_call_next_broadcasts` | Call next triggers patient_called |
| `test_settings_update_broadcasts` | Settings change broadcasts |
| `test_queue_reset_broadcasts` | Reset triggers queue_reset |
| `test_wait_time_calculation` | 3 patients × 10 min = 30 min |
| `test_request_state_event` | request_state returns queue_updated |

---

## Edge Case Test Matrix

| Scenario | Expected Result | Auto Test |
|----------|-----------------|-----------|
| Add with empty name | 400 error | ✅ |
| Add duplicate name | 409 error | ✅ |
| Call next, empty queue | 400 error | ✅ |
| Consultation time = 0 | 400 error | ✅ |
| Consultation time = 200 | 400 error | ✅ |
| Reset empty queue | 200, cleared = 0 | ✅ |
| Remove nonexistent | 404 error | ✅ |
| 3 waiting, avg 10 min | est wait = 30 | ✅ |
| Socket connect | receives state | ✅ |
| Multiple tabs sync | Manual | ☐ |
| Browser reconnect | Manual | ☐ |
| Simultaneous adds | Manual | ☐ |

---

## Performance Notes

- Single SQLite connection per request (context manager)
- Full state rebuild on each mutation (acceptable for clinic scale)
- WebSocket broadcast to all clients (O(n) connections)
- For 100+ concurrent connections, consider Redis adapter
