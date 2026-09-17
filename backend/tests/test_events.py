"""Tests for the event ingestion and history API."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(autouse=True)
def _sqlite_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")


def _table_event(
    zone_id: str = "t1", from_state: str = "available", to_state: str = "occupied"
) -> dict:
    return {
        "zone_id": zone_id,
        "from_state": from_state,
        "to_state": to_state,
        "occurred_at": "2024-01-01T12:00:00Z",
    }


def _camera_event(camera_id: str = "cam1", status: str = "connected") -> dict:
    return {
        "camera_id": camera_id,
        "status": status,
        "occurred_at": "2024-01-01T12:00:00Z",
    }


def _entrance_event(zone_id: str = "main", track_id: int = 1, event_type: str = "entry") -> dict:
    return {
        "zone_id": zone_id,
        "track_id": track_id,
        "event_type": event_type,
        "occurred_at": "2024-01-01T12:00:00Z",
    }


def _queue_event(zone_id: str = "queue1", track_id: int = 1, event_type: str = "entry") -> dict:
    return {
        "zone_id": zone_id,
        "track_id": track_id,
        "event_type": event_type,
        "occurred_at": "2024-01-01T12:00:00Z",
    }


def _table_session(
    zone_id: str = "t1",
    ended_at: str | None = "2024-01-01T13:00:00Z",
    peak_customer_count: int = 3,
    status: str = "completed",
) -> dict:
    return {
        "zone_id": zone_id,
        "started_at": "2024-01-01T12:00:00Z",
        "ended_at": ended_at,
        "peak_customer_count": peak_customer_count,
        "status": status,
    }


def test_ingest_table_event_returns_created_record() -> None:
    with TestClient(app) as client:
        response = client.post("/events/tables", json=_table_event())

    assert response.status_code == 201
    body = response.json()
    assert body["zone_id"] == "t1"
    assert body["from_state"] == "available"
    assert body["to_state"] == "occupied"
    assert "id" in body
    assert "received_at" in body


def test_list_table_events_returns_ingested_events() -> None:
    with TestClient(app) as client:
        client.post("/events/tables", json=_table_event(zone_id="t1"))
        client.post("/events/tables", json=_table_event(zone_id="t2"))

        response = client.get("/events/tables")

    assert response.status_code == 200
    assert {event["zone_id"] for event in response.json()} == {"t1", "t2"}


def test_list_table_events_filters_by_zone_id() -> None:
    with TestClient(app) as client:
        client.post("/events/tables", json=_table_event(zone_id="t1"))
        client.post("/events/tables", json=_table_event(zone_id="t2"))

        response = client.get("/events/tables", params={"zone_id": "t1"})

    assert response.status_code == 200
    assert [event["zone_id"] for event in response.json()] == ["t1"]


def test_ingest_camera_event_returns_created_record() -> None:
    with TestClient(app) as client:
        response = client.post("/events/cameras", json=_camera_event())

    assert response.status_code == 201
    body = response.json()
    assert body["camera_id"] == "cam1"
    assert body["status"] == "connected"
    assert "id" in body


def test_list_camera_events_filters_by_camera_id() -> None:
    with TestClient(app) as client:
        client.post("/events/cameras", json=_camera_event(camera_id="cam1"))
        client.post("/events/cameras", json=_camera_event(camera_id="cam2"))

        response = client.get("/events/cameras", params={"camera_id": "cam2"})

    assert response.status_code == 200
    assert [event["camera_id"] for event in response.json()] == ["cam2"]


def test_ingest_entrance_event_returns_created_record() -> None:
    with TestClient(app) as client:
        response = client.post("/events/entrance", json=_entrance_event())

    assert response.status_code == 201
    body = response.json()
    assert body["zone_id"] == "main"
    assert body["track_id"] == 1
    assert body["event_type"] == "entry"
    assert "id" in body


def test_list_entrance_events_filters_by_zone_id() -> None:
    with TestClient(app) as client:
        client.post("/events/entrance", json=_entrance_event(zone_id="main"))
        client.post("/events/entrance", json=_entrance_event(zone_id="side"))

        response = client.get("/events/entrance", params={"zone_id": "side"})

    assert response.status_code == 200
    assert [event["zone_id"] for event in response.json()] == ["side"]


def test_ingest_queue_event_returns_created_record() -> None:
    with TestClient(app) as client:
        response = client.post("/events/queue", json=_queue_event())

    assert response.status_code == 201
    body = response.json()
    assert body["zone_id"] == "queue1"
    assert body["track_id"] == 1
    assert body["event_type"] == "entry"
    assert "id" in body


def test_list_queue_events_filters_by_zone_id() -> None:
    with TestClient(app) as client:
        client.post("/events/queue", json=_queue_event(zone_id="queue1"))
        client.post("/events/queue", json=_queue_event(zone_id="queue2"))

        response = client.get("/events/queue", params={"zone_id": "queue2"})

    assert response.status_code == 200
    assert [event["zone_id"] for event in response.json()] == ["queue2"]


def test_ingest_table_session_returns_created_record() -> None:
    with TestClient(app) as client:
        response = client.post("/events/table-sessions", json=_table_session())

    assert response.status_code == 201
    body = response.json()
    assert body["zone_id"] == "t1"
    assert body["peak_customer_count"] == 3
    assert body["status"] == "completed"
    assert body["ended_at"] is not None
    assert "id" in body


def test_ingest_table_session_allows_null_ended_at_for_active_sessions() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/events/table-sessions", json=_table_session(ended_at=None, status="active")
        )

    assert response.status_code == 201
    body = response.json()
    assert body["ended_at"] is None
    assert body["status"] == "active"


def test_list_table_sessions_filters_by_zone_id() -> None:
    with TestClient(app) as client:
        client.post("/events/table-sessions", json=_table_session(zone_id="t1"))
        client.post("/events/table-sessions", json=_table_session(zone_id="t2"))

        response = client.get("/events/table-sessions", params={"zone_id": "t2"})

    assert response.status_code == 200
    assert [session["zone_id"] for session in response.json()] == ["t2"]
