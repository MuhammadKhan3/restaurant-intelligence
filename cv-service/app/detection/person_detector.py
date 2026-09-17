"""Runs a YOLO model and filters results down to person detections."""

import numpy as np

from app.detection.model_loader import YOLOModelLoader
from app.detection.types import Detection

PERSON_CLASS_ID = 0  # "person" in the standard COCO class list used by YOLO


class PersonDetector:
    """Detects people in a frame using a YOLO model, above a confidence threshold."""

    def __init__(self, model_loader: YOLOModelLoader, confidence_threshold: float = 0.4) -> None:
        self._model_loader = model_loader
        self._confidence_threshold = confidence_threshold

    @property
    def confidence_threshold(self) -> float:
        return self._confidence_threshold

    def detect(self, frame: np.ndarray) -> list[Detection]:
        model = self._model_loader.load()
        results = model.predict(
            frame,
            conf=self._confidence_threshold,
            classes=[PERSON_CLASS_ID],
            verbose=False,
        )

        detections: list[Detection] = []
        for result in results:
            names = result.names
            for box in result.boxes:
                x1, y1, x2, y2 = (int(value) for value in box.xyxy[0].tolist())
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                detections.append(
                    Detection(
                        bbox=(x1, y1, x2, y2),
                        confidence=confidence,
                        class_id=class_id,
                        class_name=names.get(class_id, str(class_id)),
                    )
                )

        return detections
