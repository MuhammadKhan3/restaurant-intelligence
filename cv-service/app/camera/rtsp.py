"""Video source backed by an RTSP camera stream."""

from app.camera.opencv_source import OpenCVVideoSource


class RTSPCameraSource(OpenCVVideoSource):
    def __init__(self, rtsp_url: str) -> None:
        super().__init__(rtsp_url)
