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
