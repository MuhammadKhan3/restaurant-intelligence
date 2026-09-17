"""Coordinates a video source and a person detector to produce detections."""

from app.camera.factory import create_video_source
from app.config import Settings
from app.detection.person_detector import PersonDetector
from app.detection.types import Detection


class DetectionService:
    def __init__(self, settings: Settings, detector: PersonDetector) -> None:
        self._settings = settings
        self._detector = detector

    def detect_from_configured_source(self) -> list[Detection] | None:
        """Read one frame from the configured video source and detect people.

        Returns None if a frame could not be read.
        """
        source = create_video_source(self._settings)
        source.connect()
        try:
            success, frame = source.read()
        finally:
            source.release()

        if not success or frame is None:
            return None

        return self._detector.detect(frame)
