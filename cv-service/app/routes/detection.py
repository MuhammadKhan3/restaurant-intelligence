"""Detection route: runs person detection on the configured video source."""

from fastapi import APIRouter, HTTPException, Request

from app.models.detection import DetectionResponse
from app.services.detection_service import DetectionService

router = APIRouter()


@router.get("/detections", response_model=list[DetectionResponse])
def get_detections(request: Request) -> list[DetectionResponse]:
    service = DetectionService(request.app.state.settings, request.app.state.person_detector)
    detections = service.detect_from_configured_source()

    if detections is None:
        raise HTTPException(
            status_code=503,
            detail="Unable to read a frame from the configured video source",
        )

    return [DetectionResponse.from_detection(detection) for detection in detections]
