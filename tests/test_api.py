"""Unit tests for Queue Cure 2026 API and business logic."""

import json


class TestPages:
    def test_landing_page(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Queue Cure 2026" in resp.data

    def test_dashboard_page(self, client):
        resp = client.get("/dashboard")
        assert resp.status_code == 200
        assert b"Receptionist Dashboard" in resp.data

    def test_patient_page(self, client):
        resp = client.get("/patient")
        assert resp.status_code == 200
        assert b"Now Serving" in resp.data

    def test_analytics_page(self, client):
        resp = client.get("/analytics")
        assert resp.status_code == 200
        assert b"Analytics Dashboard" in resp.data


class TestPatientsAPI:
    def test_add_patient_success(self, client):
        resp = client.post(
            "/api/patients",
            data=json.dumps({"patient_name": "John Doe"}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["patient"]["patient_name"] == "John Doe"
        assert data["patient"]["token_number"] == 1
        assert data["patient"]["status"] == "waiting"

    def test_add_patient_empty_name(self, client):
        resp = client.post(
            "/api/patients",
            data=json.dumps({"patient_name": "   "}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "required" in resp.get_json()["error"].lower()

    def test_add_patient_duplicate_name(self, client):
        client.post(
            "/api/patients",
            data=json.dumps({"patient_name": "Jane Doe"}),
            content_type="application/json",
        )
        resp = client.post(
            "/api/patients",
            data=json.dumps({"patient_name": "jane doe"}),
            content_type="application/json",
        )
        assert resp.status_code == 409

    def test_auto_increment_token(self, client):
        for name in ["Alice", "Bob", "Carol"]:
            client.post(
                "/api/patients",
                data=json.dumps({"patient_name": name}),
                content_type="application/json",
            )
        resp = client.get("/api/patients")
        waiting = resp.get_json()["waiting"]
        tokens = [p["token_number"] for p in waiting]
        assert tokens == [1, 2, 3]

    def test_call_next_success(self, client):
        client.post(
            "/api/patients",
            data=json.dumps({"patient_name": "Patient One"}),
            content_type="application/json",
        )
        resp = client.post("/api/patients/call-next")
        assert resp.status_code == 200
        assert resp.get_json()["patient"]["status"] == "called"

    def test_call_next_empty_queue(self, client):
        resp = client.post("/api/patients/call-next")
        assert resp.status_code == 400
        assert "empty" in resp.get_json()["error"].lower()

    def test_remove_patient(self, client):
        add_resp = client.post(
            "/api/patients",
            data=json.dumps({"patient_name": "Remove Me"}),
            content_type="application/json",
        )
        patient_id = add_resp.get_json()["patient"]["id"]
        resp = client.delete(f"/api/patients/{patient_id}")
        assert resp.status_code == 200
        assert resp.get_json()["patient"]["status"] == "removed"

    def test_remove_nonexistent_patient(self, client):
        resp = client.delete("/api/patients/9999")
        assert resp.status_code == 404


class TestSettingsAPI:
    def test_get_settings(self, client):
        resp = client.get("/api/settings")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "average_consultation_time" in data

    def test_update_consultation_time(self, client):
        resp = client.put(
            "/api/settings",
            data=json.dumps({"average_consultation_time": 15}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["average_consultation_time"] == 15

    def test_invalid_consultation_time(self, client):
        resp = client.put(
            "/api/settings",
            data=json.dumps({"average_consultation_time": 0}),
            content_type="application/json",
        )
        assert resp.status_code == 400

        resp = client.put(
            "/api/settings",
            data=json.dumps({"average_consultation_time": 200}),
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestQueueReset:
    def test_reset_queue(self, client):
        client.post(
            "/api/patients",
            data=json.dumps({"patient_name": "A"}),
            content_type="application/json",
        )
        client.post(
            "/api/patients",
            data=json.dumps({"patient_name": "B"}),
            content_type="application/json",
        )
        resp = client.post("/api/queue/reset")
        assert resp.status_code == 200
        state = client.get("/api/patients").get_json()
        assert state["waiting_count"] == 0


class TestAnalytics:
    def test_analytics_endpoint(self, client):
        resp = client.get("/api/analytics")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "patients_served_today" in data
        assert "completion_rate" in data
        assert "estimated_wait_minutes" in data


class TestExport:
    def test_csv_export(self, client):
        client.post(
            "/api/patients",
            data=json.dumps({"patient_name": "Export Test"}),
            content_type="application/json",
        )
        resp = client.get("/api/export")
        assert resp.status_code == 200
        assert resp.content_type.startswith("text/csv")
        assert b"Export Test" in resp.data
