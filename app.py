"""Queue Cure 2026 - Real-time clinic queue management system."""

import csv
import io
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request, Response
from flask_socketio import SocketIO, emit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "database.db"))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "queue-cure-2026-dev-key-change-in-prod")

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="eventlet",
    ping_timeout=60,
    ping_interval=25,
)

STATUS_WAITING = "waiting"
STATUS_CALLED = "called"
STATUS_SERVED = "served"
STATUS_REMOVED = "removed"

DOCTOR_AVAILABLE = "available"
DOCTOR_BUSY = "busy"
DOCTOR_OFFLINE = "offline"


def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        # Create base tables
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_number INTEGER NOT NULL,
                patient_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'waiting',
                created_at TEXT NOT NULL,
                served_at TEXT
            );

            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                average_consultation_time INTEGER NOT NULL DEFAULT 10,
                doctor_status TEXT NOT NULL DEFAULT 'available',
                clinic_name TEXT NOT NULL DEFAULT 'Queue Cure Clinic'
            );

            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );

            INSERT OR IGNORE INTO settings (id, average_consultation_time, doctor_status, clinic_name)
            VALUES (1, 10, 'available', 'Queue Cure Clinic');
            """
        )
        
        # Add new columns to settings table if they don't exist
        cursor = conn.execute("PRAGMA table_info(settings)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'peak_queue_length' not in columns:
            conn.execute("ALTER TABLE settings ADD COLUMN peak_queue_length INTEGER NOT NULL DEFAULT 0")
        if 'last_peak_reset_date' not in columns:
            conn.execute("ALTER TABLE settings ADD COLUMN last_peak_reset_date TEXT")


def log_activity(conn, action):
    conn.execute(
        "INSERT INTO activity_logs (action, timestamp) VALUES (?, ?)",
        (action, utc_now_iso()),
    )


def row_to_patient(row):
    if not row:
        return None
    return {
        "id": row["id"],
        "token_number": row["token_number"],
        "patient_name": row["patient_name"],
        "status": row["status"],
        "created_at": row["created_at"],
        "served_at": row["served_at"],
    }


def get_settings(conn):
    row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
    return {
        "average_consultation_time": row["average_consultation_time"],
        "doctor_status": row["doctor_status"],
        "clinic_name": row["clinic_name"],
        "peak_queue_length": row["peak_queue_length"],
        "last_peak_reset_date": row["last_peak_reset_date"],
    }


def get_next_token(conn):
    row = conn.execute("SELECT COALESCE(MAX(token_number), 0) AS max_token FROM patients").fetchone()
    return row["max_token"] + 1


def get_waiting_patients(conn):
    rows = conn.execute(
        """
        SELECT * FROM patients
        WHERE status = ?
        ORDER BY token_number ASC
        """,
        (STATUS_WAITING,),
    ).fetchall()
    return [row_to_patient(r) for r in rows]


def get_current_called(conn):
    row = conn.execute(
        """
        SELECT * FROM patients
        WHERE status = ?
        ORDER BY token_number DESC
        LIMIT 1
        """,
        (STATUS_CALLED,),
    ).fetchone()
    return row_to_patient(row)


def get_queue_history(conn, limit=20):
    rows = conn.execute(
        """
        SELECT * FROM patients
        WHERE status IN (?, ?, ?)
        ORDER BY
            CASE status
                WHEN 'called' THEN 1
                WHEN 'served' THEN 2
                WHEN 'removed' THEN 3
                ELSE 4
            END,
            COALESCE(served_at, created_at) DESC
        LIMIT ?
        """,
        (STATUS_CALLED, STATUS_SERVED, STATUS_REMOVED, limit),
    ).fetchall()
    return [row_to_patient(r) for r in rows]


def get_activity_logs(conn, limit=50):
    rows = conn.execute(
        "SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [{"id": r["id"], "action": r["action"], "timestamp": r["timestamp"]} for r in rows]


def compute_analytics(conn):
    today = datetime.now(timezone.utc).date().isoformat()
    settings = get_settings(conn)

    total_today = conn.execute(
        """
        SELECT COUNT(*) AS cnt FROM patients
        WHERE date(created_at) = date(?)
        """,
        (today,),
    ).fetchone()["cnt"]

    served_today = conn.execute(
        """
        SELECT COUNT(*) AS cnt FROM patients
        WHERE status = ? AND date(served_at) = date(?)
        """,
        (STATUS_SERVED, today),
    ).fetchone()["cnt"]

    removed_today = conn.execute(
        """
        SELECT COUNT(*) AS cnt FROM patients
        WHERE status = ? AND date(created_at) = date(?)
        """,
        (STATUS_REMOVED, today),
    ).fetchone()["cnt"]

    waiting = get_waiting_patients(conn)
    current = get_current_called(conn)
    patients_ahead = len(waiting)
    
    peak_queue_length = settings["peak_queue_length"]
    last_peak_reset_date = settings["last_peak_reset_date"]
    if last_peak_reset_date != today:
        peak_queue_length = 0
        conn.execute("UPDATE settings SET peak_queue_length = ?, last_peak_reset_date = ? WHERE id = 1", (peak_queue_length, today))
    if patients_ahead > peak_queue_length:
        peak_queue_length = patients_ahead
        conn.execute("UPDATE settings SET peak_queue_length = ? WHERE id = 1", (peak_queue_length,))

    avg_wait = settings["average_consultation_time"] * patients_ahead
    completion_rate = round((served_today / total_today * 100), 1) if total_today else 0.0

    return {
        "patients_served_today": served_today,
        "total_today": total_today,
        "removed_today": removed_today,
        "waiting_count": patients_ahead,
        "average_consultation_time": settings["average_consultation_time"],
        "estimated_wait_minutes": avg_wait,
        "completion_rate": completion_rate,
        "current_token": current["token_number"] if current else None,
        "current_patient": current["patient_name"] if current else None,
        "doctor_status": settings["doctor_status"],
        "peak_queue_length": peak_queue_length,
    }


def build_queue_state(conn):
    settings = get_settings(conn)
    waiting = get_waiting_patients(conn)
    current = get_current_called(conn)
    history = get_queue_history(conn)
    activity = get_activity_logs(conn)
    analytics = compute_analytics(conn)

    return {
        "settings": settings,
        "waiting": waiting,
        "current": current,
        "history": history,
        "activity": activity,
        "analytics": analytics,
        "waiting_count": len(waiting),
        "estimated_wait_minutes": settings["average_consultation_time"] * len(waiting),
    }


def broadcast_queue_update():
    with get_db() as conn:
        state = build_queue_state(conn)
    socketio.emit("queue_updated", state)
    socketio.emit("analytics_updated", state["analytics"])


def broadcast_settings_update(settings):
    socketio.emit("settings_updated", settings)


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------


@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/patient")
def patient_view():
    return render_template("patient.html")


@app.route("/analytics")
def analytics_view():
    return render_template("analytics.html")


# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------


@app.route("/api/patients", methods=["GET"])
def api_get_patients():
    with get_db() as conn:
        state = build_queue_state(conn)
    return jsonify(state)


@app.route("/api/patients", methods=["POST"])
def api_add_patient():
    data = request.get_json(silent=True) or {}
    name = (data.get("patient_name") or "").strip()

    if not name:
        return jsonify({"error": "Patient name is required."}), 400
    if len(name) > 100:
        return jsonify({"error": "Patient name must be 100 characters or fewer."}), 400

    with get_db() as conn:
        duplicate = conn.execute(
            """
            SELECT id FROM patients
            WHERE lower(patient_name) = lower(?) AND status IN (?, ?)
            """,
            (name, STATUS_WAITING, STATUS_CALLED),
        ).fetchone()
        if duplicate:
            return jsonify({"error": f"'{name}' is already in the queue."}), 409

        token = get_next_token(conn)
        now = utc_now_iso()
        cursor = conn.execute(
            """
            INSERT INTO patients (token_number, patient_name, status, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (token, name, STATUS_WAITING, now),
        )
        patient_id = cursor.lastrowid
        log_activity(conn, f"Patient added: {name} (Token QC-{str(token).zfill(3)})")
        patient = row_to_patient(
            conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        )

    socketio.emit("patient_added", patient)
    broadcast_queue_update()
    return jsonify({"patient": patient}), 201


@app.route("/api/patients/<int:patient_id>/call", methods=["POST"])
def api_call_patient(patient_id):
    with get_db() as conn:
        patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        if not patient:
            return jsonify({"error": "Patient not found."}), 404
        if patient["status"] != STATUS_WAITING:
            return jsonify({"error": "Only waiting patients can be called."}), 400

        now = utc_now_iso()
        conn.execute(
            """
            UPDATE patients SET status = ?, served_at = ?
            WHERE status = ?
            """,
            (STATUS_SERVED, now, STATUS_CALLED),
        )
        conn.execute(
            "UPDATE patients SET status = ?, served_at = ? WHERE id = ?",
            (STATUS_CALLED, now, patient_id),
        )
        conn.execute("UPDATE settings SET doctor_status = ? WHERE id = 1", (DOCTOR_BUSY,))
        log_activity(
            conn,
            f"Patient called: {patient['patient_name']} (Token QC-{str(patient['token_number']).zfill(3)})",
        )
        called = row_to_patient(
            conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        )

    socketio.emit("patient_called", called)
    broadcast_queue_update()
    return jsonify({"patient": called})


@app.route("/api/patients/call-next", methods=["POST"])
def api_call_next():
    with get_db() as conn:
        next_patient = conn.execute(
            """
            SELECT * FROM patients
            WHERE status = ?
            ORDER BY token_number ASC
            LIMIT 1
            """,
            (STATUS_WAITING,),
        ).fetchone()
        if not next_patient:
            return jsonify({"error": "Queue is empty. No patients to call."}), 400

        now = utc_now_iso()
        conn.execute(
            """
            UPDATE patients SET status = ?, served_at = ?
            WHERE status = ?
            """,
            (STATUS_SERVED, now, STATUS_CALLED),
        )
        conn.execute(
            "UPDATE patients SET status = ?, served_at = ? WHERE id = ?",
            (STATUS_CALLED, now, next_patient["id"]),
        )
        conn.execute("UPDATE settings SET doctor_status = ? WHERE id = 1", (DOCTOR_BUSY,))
        log_activity(
            conn,
            f"Patient called: {next_patient['patient_name']} (Token QC-{str(next_patient['token_number']).zfill(3)})",
        )
        called = row_to_patient(
            conn.execute("SELECT * FROM patients WHERE id = ?", (next_patient["id"],)).fetchone()
        )

    socketio.emit("patient_called", called)
    broadcast_queue_update()
    return jsonify({"patient": called})


@app.route("/api/patients/<int:patient_id>", methods=["DELETE"])
def api_remove_patient(patient_id):
    with get_db() as conn:
        patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        if not patient:
            return jsonify({"error": "Patient not found."}), 404
        if patient["status"] not in (STATUS_WAITING, STATUS_CALLED):
            return jsonify({"error": "Patient cannot be removed in current status."}), 400

        now = utc_now_iso()
        conn.execute(
            "UPDATE patients SET status = ?, served_at = ? WHERE id = ?",
            (STATUS_REMOVED, now, patient_id),
        )
        if patient["status"] == STATUS_CALLED:
            conn.execute("UPDATE settings SET doctor_status = ? WHERE id = 1", (DOCTOR_AVAILABLE,))
        log_activity(
            conn,
            f"Patient removed: {patient['patient_name']} (Token QC-{str(patient['token_number']).zfill(3)})",
        )
        removed = row_to_patient(
            conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        )

    socketio.emit("patient_removed", removed)
    broadcast_queue_update()
    return jsonify({"patient": removed})


@app.route("/api/patients/<int:patient_id>/complete", methods=["POST"])
def api_complete_consultation(patient_id):
    with get_db() as conn:
        patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        if not patient:
            return jsonify({"error": "Patient not found."}), 404
        if patient["status"] != STATUS_CALLED:
            return jsonify({"error": "Only the currently called patient can be completed."}), 400

        now = utc_now_iso()
        conn.execute(
            "UPDATE patients SET status = ?, served_at = ? WHERE id = ?",
            (STATUS_SERVED, now, patient_id),
        )
        conn.execute("UPDATE settings SET doctor_status = ? WHERE id = 1", (DOCTOR_AVAILABLE,))
        log_activity(
            conn,
            f"Consultation completed: {patient['patient_name']} (Token QC-{str(patient['token_number']).zfill(3)})",
        )
        served = row_to_patient(
            conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        )

    broadcast_queue_update()
    return jsonify({"patient": served})


@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    with get_db() as conn:
        settings = get_settings(conn)
    return jsonify(settings)


@app.route("/api/settings", methods=["PUT"])
def api_update_settings():
    data = request.get_json(silent=True) or {}
    updates = {}

    if "average_consultation_time" in data:
        try:
            avg_time = int(data["average_consultation_time"])
        except (TypeError, ValueError):
            return jsonify({"error": "Average consultation time must be a valid integer."}), 400
        if avg_time < 1 or avg_time > 120:
            return jsonify({"error": "Average consultation time must be between 1 and 120 minutes."}), 400
        updates["average_consultation_time"] = avg_time

    if "doctor_status" in data:
        status = data["doctor_status"]
        if status not in (DOCTOR_AVAILABLE, DOCTOR_BUSY, DOCTOR_OFFLINE):
            return jsonify({"error": "Invalid doctor status."}), 400
        updates["doctor_status"] = status

    if "clinic_name" in data:
        name = (data["clinic_name"] or "").strip()
        if not name:
            return jsonify({"error": "Clinic name cannot be empty."}), 400
        updates["clinic_name"] = name[:100]

    if not updates:
        return jsonify({"error": "No valid settings provided."}), 400

    with get_db() as conn:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(f"UPDATE settings SET {set_clause} WHERE id = 1", tuple(updates.values()))
        if "average_consultation_time" in updates:
            log_activity(conn, f"Consultation time set to {updates['average_consultation_time']} min")
        settings = get_settings(conn)

    broadcast_settings_update(settings)
    broadcast_queue_update()
    return jsonify(settings)


@app.route("/api/queue/reset", methods=["POST"])
def api_reset_queue():
    with get_db() as conn:
        waiting_count = conn.execute(
            "SELECT COUNT(*) AS cnt FROM patients WHERE status IN (?, ?)",
            (STATUS_WAITING, STATUS_CALLED),
        ).fetchone()["cnt"]
        conn.execute(
            """
            UPDATE patients SET status = ?, served_at = ?
            WHERE status IN (?, ?)
            """,
            (STATUS_REMOVED, utc_now_iso(), STATUS_WAITING, STATUS_CALLED),
        )
        conn.execute("UPDATE settings SET doctor_status = ? WHERE id = 1", (DOCTOR_AVAILABLE,))
        log_activity(conn, f"Queue reset ({waiting_count} patients cleared)")

    socketio.emit("queue_reset", {"message": "Queue has been reset."})
    broadcast_queue_update()
    return jsonify({"message": "Queue reset successfully.", "cleared": waiting_count})


@app.route("/api/analytics", methods=["GET"])
def api_analytics():
    with get_db() as conn:
        analytics = compute_analytics(conn)
    return jsonify(analytics)


@app.route("/api/export", methods=["GET"])
def api_export():
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT token_number, patient_name, status, created_at, served_at
            FROM patients
            ORDER BY created_at DESC
            """
        ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Token", "Patient Name", "Status", "Created At", "Served At"])
    for row in rows:
        writer.writerow(
            [row["token_number"], row["patient_name"], row["status"], row["created_at"], row["served_at"]]
        )

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=queue_cure_export.csv"},
    )


# ---------------------------------------------------------------------------
# Socket.IO events
# ---------------------------------------------------------------------------


@socketio.on("connect")
def handle_connect():
    with get_db() as conn:
        state = build_queue_state(conn)
    emit("queue_updated", state)
    emit("analytics_updated", state["analytics"])


@socketio.on("request_state")
def handle_request_state():
    with get_db() as conn:
        state = build_queue_state(conn)
    emit("queue_updated", state)
    emit("analytics_updated", state["analytics"])


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
