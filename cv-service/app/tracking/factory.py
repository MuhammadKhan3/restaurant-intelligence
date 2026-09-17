"""Builds the configured ByteTracker from application settings."""

from app.config import Settings
from app.detection.model_loader import YOLOModelLoader
from app.tracking.byte_tracker import ByteTracker


def create_person_tracker(settings: Settings) -> ByteTracker:
    model_loader = YOLOModelLoader(settings.yolo_model)
    return ByteTracker(model_loader, confidence_threshold=settings.confidence_threshold)
