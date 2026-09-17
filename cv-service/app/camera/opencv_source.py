"""Shared OpenCV VideoCapture-backed implementation of VideoSource."""

import logging

import cv2
import numpy as np

from app.camera.base import ConnectionStatus, VideoSource

logger = logging.getLogger(__name__)


class OpenCVVideoSource(VideoSource):
    """VideoSource backed by cv2.VideoCapture.

    `source` is whatever cv2.VideoCapture accepts: a file path, an RTSP/HTTP
    URL, or a webcam device index.
    """

    def __init__(self, source: str | int) -> None:
        super().__init__()
        self._source = source
        self._capture: cv2.VideoCapture | None = None

    def connect(self) -> None:
        self._status = ConnectionStatus.CONNECTING
        self._capture = cv2.VideoCapture(self._source)

        if self._capture.isOpened():
            self._status = ConnectionStatus.CONNECTED
        else:
            self._status = ConnectionStatus.ERROR
            logger.error("Failed to open video source: %s", self._source)

    def read(self) -> tuple[bool, np.ndarray | None]:
        if self._capture is None or not self._capture.isOpened():
            return False, None

        success, frame = self._capture.read()
        if not success:
            self._status = ConnectionStatus.ERROR
        return success, frame

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        self._status = ConnectionStatus.DISCONNECTED
