"""API response models for detection endpoints."""

from pydantic import BaseModel

from app.detection.types import Detection


class DetectionResponse(BaseModel):
    bbox: tuple[int, int, int, int]
    confidence: float
    class_id: int
    class_name: str

    @classmethod
    def from_detection(cls, detection: Detection) -> "DetectionResponse":
        return cls(
            bbox=detection.bbox,
            confidence=detection.confidence,
            class_id=detection.class_id,
            class_name=detection.class_name,
        )
