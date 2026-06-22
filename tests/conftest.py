"""Pytest configuration and fixtures for Queue Cure 2026."""

import os
import tempfile

import pytest

# Use a temporary database before importing the app
_test_db_fd, _test_db_path = tempfile.mkstemp(suffix=".db")
os.close(_test_db_fd)
os.environ["DATABASE_PATH"] = _test_db_path
os.environ["SECRET_KEY"] = "test-secret-key"

from app import app, init_db, socketio  # noqa: E402


@pytest.fixture
def client():
    init_db()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def socket_client(client):
    return socketio.test_client(app)


@pytest.fixture(autouse=True)
def reset_db():
    init_db()
    from app import get_db

    with get_db() as conn:
        conn.execute("DELETE FROM patients")
        conn.execute("DELETE FROM activity_logs")
        conn.execute(
            "UPDATE settings SET average_consultation_time = 10, doctor_status = 'available', clinic_name = 'Test Clinic' WHERE id = 1"
        )
    yield
