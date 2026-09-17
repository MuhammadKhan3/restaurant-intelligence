"""Video source backed by a local webcam device."""

from app.camera.opencv_source import OpenCVVideoSource


class WebcamSource(OpenCVVideoSource):
    def __init__(self, device_index: int = 0) -> None:
        super().__init__(device_index)
