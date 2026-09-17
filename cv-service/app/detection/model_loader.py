"""Loads and caches a YOLO model."""

import logging

from ultralytics import YOLO

logger = logging.getLogger(__name__)


class YOLOModelLoader:
    """Lazily loads a YOLO model and keeps it cached for reuse."""

    def __init__(self, model_path: str) -> None:
        self._model_path = model_path
        self._model: YOLO | None = None

    @property
    def model_path(self) -> str:
        return self._model_path

    def load(self) -> YOLO:
        if self._model is None:
            logger.info("Loading YOLO model: %s", self._model_path)
            self._model = YOLO(self._model_path)
        return self._model
