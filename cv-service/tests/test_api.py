"""Tests for the FastAPI routes."""

import pytest
from fastapi.testclient import TestClient

from app.camera.base import ConnectionStatus
from app.detection.types import Detection
from app.main import app


def test_health_endpoint_reports_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_detections_endpoint_returns_503_when_source_unavailable() -> None:
    with TestClient(app) as client:
        response = client.get("/detections")

    assert response.status_code == 503


class _FakeSource:
    def connect(self) -> None:
        pass

    def read(self) -> tuple[bool, object]:
        return True, object()

    def release(self) -> None:
        pass

    @property
    def is_connected(self) -> bool:
        return True

    @property
    def status(self) -> ConnectionStatus:
        return ConnectionStatus.CONNECTED


class _FakeDetector:
    def __init__(self, detections: list[Detection]) -> None:
        self._detections = detections

    def detect(self, frame: object) -> list[Detection]:
        return self._detections


def test_detections_endpoint_returns_detections(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_detections = [
        Detection(bbox=(1, 2, 3, 4), confidence=0.9, class_id=0, class_name="person")
    ]

    monkeypatch.setattr(
        "app.services.detection_service.create_video_source",
        lambda settings: _FakeSource(),
    )

    with TestClient(app) as client:
        client.app.state.person_detector = _FakeDetector(fake_detections)
        response = client.get("/detections")

    assert response.status_code == 200
    assert response.json() == [
        {"bbox": [1, 2, 3, 4], "confidence": 0.9, "class_id": 0, "class_name": "person"}
    ]
