"""Tests for the detection module: model loading, person detection, visualization."""

from unittest.mock import MagicMock, patch

import numpy as np

from app.config import Settings
from app.detection.factory import create_person_detector
from app.detection.model_loader import YOLOModelLoader
from app.detection.person_detector import PERSON_CLASS_ID, PersonDetector
from app.detection.types import Detection
from app.detection.visualization import draw_detections


@patch("app.detection.model_loader.YOLO")
def test_model_loader_loads_and_caches_model(mock_yolo_cls: MagicMock) -> None:
    mock_model = MagicMock()
    mock_yolo_cls.return_value = mock_model

    loader = YOLOModelLoader("yolov8n.pt")
    first = loader.load()
    second = loader.load()

    assert first is mock_model
    assert second is mock_model
    mock_yolo_cls.assert_called_once_with("yolov8n.pt")


def _mock_box(xyxy: list[float], confidence: float, class_id: int) -> MagicMock:
    box = MagicMock()
    box.xyxy = [MagicMock(tolist=MagicMock(return_value=xyxy))]
    box.conf = [confidence]
    box.cls = [class_id]
    return box


@patch("app.detection.model_loader.YOLO")
def test_person_detector_filters_and_maps_results(mock_yolo_cls: MagicMock) -> None:
    mock_model = MagicMock()
    mock_model.predict.return_value = [
        MagicMock(
            names={0: "person"},
            boxes=[_mock_box([10.0, 20.0, 30.0, 40.0], 0.87, 0)],
        )
    ]
    mock_yolo_cls.return_value = mock_model

    detector = PersonDetector(YOLOModelLoader("yolov8n.pt"), confidence_threshold=0.5)
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    detections = detector.detect(frame)

    assert len(detections) == 1
    detection = detections[0]
    assert detection.bbox == (10, 20, 30, 40)
    assert detection.confidence == 0.87
    assert detection.class_id == 0
    assert detection.class_name == "person"
    mock_model.predict.assert_called_once_with(
        frame, conf=0.5, classes=[PERSON_CLASS_ID], verbose=False
    )


def test_draw_detections_annotates_a_copy_without_mutating_original() -> None:
    frame = np.zeros((50, 50, 3), dtype=np.uint8)
    original = frame.copy()
    detection = Detection(bbox=(5, 5, 20, 20), confidence=0.9, class_id=0, class_name="person")

    annotated = draw_detections(frame, [detection])

    assert annotated.shape == frame.shape
    assert not np.array_equal(annotated, frame)
    assert np.array_equal(frame, original)


def test_create_person_detector_uses_settings() -> None:
    settings = Settings(_env_file=None, yolo_model="custom.pt", confidence_threshold=0.6)

    detector = create_person_detector(settings)

    assert isinstance(detector, PersonDetector)
    assert detector.confidence_threshold == 0.6
