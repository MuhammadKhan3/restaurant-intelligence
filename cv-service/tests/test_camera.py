"""Tests for the camera module: sources, status, and the frame pipeline."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.camera.base import ConnectionStatus, VideoSource
from app.camera.factory import create_video_source
from app.camera.local_file import LocalVideoFileSource
from app.camera.pipeline import FrameProcessingPipeline
from app.camera.rtsp import RTSPCameraSource
from app.camera.webcam import WebcamSource
from app.config import Settings


def _mock_capture(*, opened: bool, frames: list[np.ndarray] | None = None) -> MagicMock:
    capture = MagicMock()
    capture.isOpened.return_value = opened

    if frames is not None:
        results = [(True, frame) for frame in frames] + [(False, None)]
        capture.read.side_effect = results

    return capture


@patch("app.camera.opencv_source.cv2.VideoCapture")
def test_local_file_source_connects_successfully(mock_video_capture: MagicMock) -> None:
    mock_video_capture.return_value = _mock_capture(opened=True)

    source = LocalVideoFileSource("sample.mp4")
    source.connect()

    assert source.status == ConnectionStatus.CONNECTED
    assert source.is_connected
    mock_video_capture.assert_called_once_with("sample.mp4")


@patch("app.camera.opencv_source.cv2.VideoCapture")
def test_source_connection_error_when_capture_fails_to_open(
    mock_video_capture: MagicMock,
) -> None:
    mock_video_capture.return_value = _mock_capture(opened=False)

    source = LocalVideoFileSource("missing.mp4")
    source.connect()

    assert source.status == ConnectionStatus.ERROR
    assert not source.is_connected


@patch("app.camera.opencv_source.cv2.VideoCapture")
def test_webcam_source_uses_device_index(mock_video_capture: MagicMock) -> None:
    mock_video_capture.return_value = _mock_capture(opened=True)

    source = WebcamSource(device_index=1)
    source.connect()

    mock_video_capture.assert_called_once_with(1)


@patch("app.camera.opencv_source.cv2.VideoCapture")
def test_rtsp_source_uses_stream_url(mock_video_capture: MagicMock) -> None:
    mock_video_capture.return_value = _mock_capture(opened=True)

    url = "rtsp://camera.local/stream"
    source = RTSPCameraSource(url)
    source.connect()

    mock_video_capture.assert_called_once_with(url)


@patch("app.camera.opencv_source.cv2.VideoCapture")
def test_release_resets_status_to_disconnected(mock_video_capture: MagicMock) -> None:
    mock_video_capture.return_value = _mock_capture(opened=True)

    source = LocalVideoFileSource("sample.mp4")
    source.connect()
    source.release()

    assert source.status == ConnectionStatus.DISCONNECTED
    assert not source.is_connected


def test_create_video_source_selects_local_file() -> None:
    settings = Settings(_env_file=None, video_source_type="video", video_source="clip.mp4")

    source = create_video_source(settings)

    assert isinstance(source, LocalVideoFileSource)


def test_create_video_source_selects_webcam() -> None:
    settings = Settings(_env_file=None, video_source_type="webcam", video_source="0")

    source = create_video_source(settings)

    assert isinstance(source, WebcamSource)


def test_create_video_source_selects_rtsp() -> None:
    settings = Settings(
        _env_file=None,
        video_source_type="rtsp",
        video_source="rtsp://camera.local/stream",
    )

    source = create_video_source(settings)

    assert isinstance(source, RTSPCameraSource)


def test_create_video_source_rejects_unknown_type() -> None:
    settings = Settings(_env_file=None, video_source_type="unknown")

    with pytest.raises(ValueError):
        create_video_source(settings)


class _FakeVideoSource(VideoSource):
    """In-memory VideoSource for pipeline tests, independent of OpenCV."""

    def __init__(self, frames: list[np.ndarray]) -> None:
        super().__init__()
        self._frames = frames

    def connect(self) -> None:
        self._status = ConnectionStatus.CONNECTED

    def read(self) -> tuple[bool, np.ndarray | None]:
        if not self._frames:
            return False, None
        return True, self._frames.pop(0)

    def release(self) -> None:
        self._status = ConnectionStatus.DISCONNECTED


def test_pipeline_yields_all_frames_from_source() -> None:
    frames = [np.zeros((2, 2)), np.ones((2, 2))]
    pipeline = FrameProcessingPipeline(_FakeVideoSource(list(frames)))

    result = list(pipeline.frames())

    assert len(result) == 2
    assert np.array_equal(result[0], frames[0])
    assert np.array_equal(result[1], frames[1])


def test_pipeline_applies_processors_in_order() -> None:
    source = _FakeVideoSource([np.zeros((1, 1))])
    pipeline = FrameProcessingPipeline(source)
    pipeline.add_processor(lambda frame: frame + 1)
    pipeline.add_processor(lambda frame: frame * 10)

    (result,) = list(pipeline.frames())

    assert result.item() == 10


def test_pipeline_releases_source_after_exhausting_frames() -> None:
    source = _FakeVideoSource([np.zeros((1, 1))])
    pipeline = FrameProcessingPipeline(source)

    list(pipeline.frames())

    assert source.status == ConnectionStatus.DISCONNECTED
