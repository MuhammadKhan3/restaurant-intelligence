"""Video source backed by a local video file."""

from app.camera.opencv_source import OpenCVVideoSource


class LocalVideoFileSource(OpenCVVideoSource):
    def __init__(self, file_path: str) -> None:
        super().__init__(file_path)
