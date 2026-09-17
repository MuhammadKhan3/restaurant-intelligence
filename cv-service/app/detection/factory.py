"""Builds the configured PersonDetector from application settings."""

from app.config import Settings
from app.detection.model_loader import YOLOModelLoader
from app.detection.person_detector import PersonDetector


def create_person_detector(settings: Settings) -> PersonDetector:
    model_loader = YOLOModelLoader(settings.yolo_model)
    return PersonDetector(model_loader, confidence_threshold=settings.confidence_threshold)
