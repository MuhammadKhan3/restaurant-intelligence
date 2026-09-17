"""Tests for the table zone configuration API: CRUD, persisted to disk."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(autouse=True)
def _zones_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    zones_file = tmp_path / "table_zones.json"
    monkeypatch.setenv("TABLE_ZONES_FILE", str(zones_file))
    return zones_file


def _zone(zone_id: str = "t1", capacity: int = 4) -> dict:
    return {
        "id": zone_id,
        "name": "Table 1",
        "capacity": capacity,
        "points": [[0, 0], [10, 0], [10, 10], [0, 10]],
    }


def test_list_table_zones_starts_empty() -> None:
    with TestClient(app) as client:
        response = client.get("/table-zones")

    assert response.status_code == 200
    assert response.json() == []


def test_create_table_zone_persists_to_disk(_zones_file: Path) -> None:
    with TestClient(app) as client:
        response = client.post("/table-zones", json=_zone())

    assert response.status_code == 201
    assert response.json()["id"] == "t1"
    assert _zones_file.exists()


def test_create_table_zone_rejects_duplicate_id() -> None:
    with TestClient(app) as client:
        client.post("/table-zones", json=_zone())
        response = client.post("/table-zones", json=_zone())

    assert response.status_code == 409


def test_get_table_zone_returns_404_when_missing() -> None:
    with TestClient(app) as client:
        response = client.get("/table-zones/missing")

    assert response.status_code == 404


def test_get_table_zone_returns_created_zone() -> None:
    with TestClient(app) as client:
        client.post("/table-zones", json=_zone())
        response = client.get("/table-zones/t1")

    assert response.status_code == 200
    assert response.json()["capacity"] == 4


def test_update_table_zone_replaces_it() -> None:
    with TestClient(app) as client:
        client.post("/table-zones", json=_zone())
        response = client.put("/table-zones/t1", json=_zone(capacity=6))

    assert response.status_code == 200
    assert response.json()["capacity"] == 6


def test_update_table_zone_returns_404_when_missing() -> None:
    with TestClient(app) as client:
        response = client.put("/table-zones/missing", json=_zone(zone_id="missing"))

    assert response.status_code == 404


def test_delete_table_zone_removes_it() -> None:
    with TestClient(app) as client:
        client.post("/table-zones", json=_zone())
        delete_response = client.delete("/table-zones/t1")
        get_response = client.get("/table-zones/t1")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_delete_table_zone_returns_404_when_missing() -> None:
    with TestClient(app) as client:
        response = client.delete("/table-zones/missing")

    assert response.status_code == 404


def test_zones_reload_from_disk_on_restart(_zones_file: Path) -> None:
    with TestClient(app) as client:
        client.post("/table-zones", json=_zone())

    with TestClient(app) as client:
        response = client.get("/table-zones")

    assert [zone["id"] for zone in response.json()] == ["t1"]
