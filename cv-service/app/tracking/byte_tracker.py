"""Person tracker using Ultralytics' built-in ByteTrack integration."""

import numpy as np

from app.detection.model_loader import YOLOModelLoader
from app.detection.person_detector import PERSON_CLASS_ID
from app.tracking.base import Tracker
from app.tracking.types import Track


class ByteTracker(Tracker):
    """Tracks people across frames using YOLO + ByteTrack (via ultralytics)."""

    def __init__(self, model_loader: YOLOModelLoader, confidence_threshold: float = 0.4) -> None:
        self._model_loader = model_loader
        self._confidence_threshold = confidence_threshold
        self._persist = False

    def update(self, frame: np.ndarray) -> list[Track]:
        model = self._model_loader.load()
        results = model.track(
            frame,
            persist=self._persist,
            tracker="bytetrack.yaml",
            conf=self._confidence_threshold,
            classes=[PERSON_CLASS_ID],
            verbose=False,
        )
        self._persist = True

        tracks: list[Track] = []
        for result in results:
            boxes = result.boxes
            if boxes is None or boxes.id is None:
                continue

            names = result.names
            track_ids = boxes.id.tolist()

            for box, track_id in zip(boxes, track_ids, strict=True):
                x1, y1, x2, y2 = (int(value) for value in box.xyxy[0].tolist())
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                tracks.append(
                    Track(
                        track_id=int(track_id),
                        bbox=(x1, y1, x2, y2),
                        confidence=confidence,
                        class_id=class_id,
                        class_name=names.get(class_id, str(class_id)),
                    )
                )

        return tracks

    def reset(self) -> None:
        self._persist = False
