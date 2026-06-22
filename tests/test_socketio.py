"""Integration tests for Queue Cure 2026 WebSocket events."""

import json
import time


class TestSocketIOIntegration:
    def test_connect_receives_state(self, socket_client):
        received = socket_client.get_received()
        events = [e for e in received if e["name"] == "queue_updated"]
        assert len(events) >= 1
        state = events[0]["args"][0]
        assert "waiting" in state
        assert "settings" in state

    def test_patient_added_broadcasts(self, client, socket_client):
        socket_client.get_received()  # clear
        client.post(
            "/api/patients",
            data=json.dumps({"patient_name": "Socket Patient"}),
            content_type="application/json",
        )
        time.sleep(0.1)
        received = socket_client.get_received()
        names = [e["name"] for e in received]
        assert "patient_added" in names
        assert "queue_updated" in names

    def test_call_next_broadcasts(self, client, socket_client):
        client.post(
            "/api/patients",
            data=json.dumps({"patient_name": "Call Test"}),
            content_type="application/json",
        )
        socket_client.get_received()
        client.post("/api/patients/call-next")
        time.sleep(0.1)
        received = socket_client.get_received()
        names = [e["name"] for e in received]
        assert "patient_called" in names
        assert "queue_updated" in names

    def test_settings_update_broadcasts(self, client, socket_client):
        socket_client.get_received()
        client.put(
            "/api/settings",
            data=json.dumps({"average_consultation_time": 20}),
            content_type="application/json",
        )
        time.sleep(0.1)
        received = socket_client.get_received()
        names = [e["name"] for e in received]
        assert "settings_updated" in names
        assert "queue_updated" in names

    def test_queue_reset_broadcasts(self, client, socket_client):
        client.post(
            "/api/patients",
            data=json.dumps({"patient_name": "Reset Test"}),
            content_type="application/json",
        )
        socket_client.get_received()
        client.post("/api/queue/reset")
        time.sleep(0.1)
        received = socket_client.get_received()
        names = [e["name"] for e in received]
        assert "queue_reset" in names
        assert "queue_updated" in names

    def test_wait_time_calculation(self, client):
        client.put(
            "/api/settings",
            data=json.dumps({"average_consultation_time": 10}),
            content_type="application/json",
        )
        for name in ["P1", "P2", "P3"]:
            client.post(
                "/api/patients",
                data=json.dumps({"patient_name": name}),
                content_type="application/json",
            )
        state = client.get("/api/patients").get_json()
        assert state["waiting_count"] == 3
        assert state["estimated_wait_minutes"] == 30

    def test_request_state_event(self, socket_client):
        socket_client.emit("request_state")
        time.sleep(0.1)
        received = socket_client.get_received()
        assert any(e["name"] == "queue_updated" for e in received)
