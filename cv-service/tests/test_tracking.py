"""Tests for the tracking module: ByteTracker, lifecycle, visualization."""

from unittest.mock import MagicMock, patch

import numpy as np

from app.config import Settings
from app.tracking.byte_tracker import ByteTracker
from app.tracking.factory import create_person_tracker
from app.tracking.lifecycle import TrackLifecycleManager
from app.tracking.types import Track, TrackState
from app.tracking.visualization import draw_tracks


def _mock_box(xyxy: list[float], confidence: float, class_id: int) -> MagicMock:
    box = MagicMock()
    box.xyxy = [MagicMock(tolist=MagicMock(return_value=xyxy))]
    box.conf = [confidence]
    box.cls = [class_id]
    return box


def _mock_boxes(entries: list[tuple[list[float], float, int, int]]) -> MagicMock:
    boxes = MagicMock()
    boxes.__iter__ = lambda self: iter(
        [_mock_box(xyxy, conf, class_id) for xyxy, conf, class_id, _track_id in entries]
    )
    boxes.id = MagicMock(tolist=MagicMock(return_value=[track_id for *_, track_id in entries]))
    return boxes


@patch("app.detection.model_loader.YOLO")
def test_byte_tracker_maps_results_to_tracks(mock_yolo_cls: MagicMock) -> None:
    mock_model = MagicMock()
    mock_model.track.return_value = [
        MagicMock(
            names={0: "person"},
            boxes=_mock_boxes([([10.0, 20.0, 30.0, 40.0], 0.9, 0, 7)]),
        )
    ]
    mock_yolo_cls.return_value = mock_model

    from app.detection.model_loader import YOLOModelLoader

    tracker = ByteTracker(YOLOModelLoader("yolov8n.pt"), confidence_threshold=0.5)
    tracks = tracker.update(np.zeros((10, 10, 3), dtype=np.uint8))

    assert len(tracks) == 1
    track = tracks[0]
    assert track.track_id == 7
    assert track.bbox == (10, 20, 30, 40)
    assert track.confidence == 0.9
    assert track.class_name == "person"


@patch("app.detection.model_loader.YOLO")
def test_byte_tracker_skips_persist_on_first_call_then_persists(
    mock_yolo_cls: MagicMock,
) -> None:
    mock_model = MagicMock()
    mock_model.track.return_value = [MagicMock(names={}, boxes=None)]
    mock_yolo_cls.return_value = mock_model

    from app.detection.model_loader import YOLOModelLoader

    tracker = ByteTracker(YOLOModelLoader("yolov8n.pt"))
    frame = np.zeros((10, 10, 3), dtype=np.uint8)

    tracker.update(frame)
    tracker.update(frame)

    first_call_kwargs = mock_model.track.call_args_list[0].kwargs
    second_call_kwargs = mock_model.track.call_args_list[1].kwargs
    assert first_call_kwargs["persist"] is False
    assert second_call_kwargs["persist"] is True

    tracker.reset()
    tracker.update(frame)
    third_call_kwargs = mock_model.track.call_args_list[2].kwargs
    assert third_call_kwargs["persist"] is False


def test_create_person_tracker_uses_settings() -> None:
    settings = Settings(_env_file=None, yolo_model="custom.pt", confidence_threshold=0.6)

    tracker = create_person_tracker(settings)

    assert isinstance(tracker, ByteTracker)


def _track(track_id: int) -> Track:
    return Track(
        track_id=track_id, bbox=(0, 0, 1, 1), confidence=0.9, class_id=0, class_name="person"
    )


def test_lifecycle_manager_marks_missing_tracks_lost_then_removed() -> None:
    manager = TrackLifecycleManager(max_lost_frames=1)

    manager.update([_track(1)])
    records_after_lost = manager.update([])
    assert records_after_lost[0].state == TrackState.LOST

    records_after_removed = manager.update([])
    assert records_after_removed == []


def test_lifecycle_manager_reactivates_a_track_that_reappears() -> None:
    manager = TrackLifecycleManager(max_lost_frames=5)

    manager.update([_track(1)])
    manager.update([])
    records = manager.update([_track(1)])

    assert len(records) == 1
    assert records[0].state == TrackState.ACTIVE
    assert records[0].frames_since_seen == 0


def test_active_tracks_excludes_lost_tracks() -> None:
    manager = TrackLifecycleManager(max_lost_frames=5)

    manager.update([_track(1), _track(2)])
    manager.update([_track(1)])

    assert [record.track_id for record in manager.active_tracks()] == [1]


def test_draw_tracks_annotates_a_copy_without_mutating_original() -> None:
    frame = np.zeros((50, 50, 3), dtype=np.uint8)
    original = frame.copy()
    track = _track(1)

    annotated = draw_tracks(frame, [track])

    assert annotated.shape == frame.shape
    assert not np.array_equal(annotated, frame)
    assert np.array_equal(frame, original)
