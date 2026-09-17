"""Build the configured VideoSource from application settings."""

from app.camera.base import VideoSource
from app.camera.local_file import LocalVideoFileSource
from app.camera.rtsp import RTSPCameraSource
from app.camera.webcam import WebcamSource
from app.config import Settings


def create_video_source(settings: Settings) -> VideoSource:
    """Create the VideoSource matching settings.video_source_type."""

    source_type = settings.video_source_type.lower()

    if source_type == "video":
        return LocalVideoFileSource(settings.video_source)

    if source_type == "webcam":
        device_index = int(settings.video_source) if settings.video_source else 0
        return WebcamSource(device_index)

    if source_type == "rtsp":
        return RTSPCameraSource(settings.video_source)

    raise ValueError(f"Unsupported VIDEO_SOURCE_TYPE: {settings.video_source_type}")
