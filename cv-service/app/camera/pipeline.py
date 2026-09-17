"""Pull frames from a VideoSource through an ordered chain of processors."""

from collections.abc import Callable, Iterator

import numpy as np

from app.camera.base import VideoSource

FrameProcessor = Callable[[np.ndarray], np.ndarray]


class FrameProcessingPipeline:
    """Connects a VideoSource to a sequence of frame processors.

    No processors are implemented yet -- this only provides the plumbing
    that future CV stages (person detection, tracking, etc.) will register
    into via `add_processor`.
    """

    def __init__(
        self,
        source: VideoSource,
        processors: list[FrameProcessor] | None = None,
    ) -> None:
        self._source = source
        self._processors = list(processors) if processors else []

    def add_processor(self, processor: FrameProcessor) -> None:
        self._processors.append(processor)

    def frames(self) -> Iterator[np.ndarray]:
        if not self._source.is_connected:
            self._source.connect()

        try:
            while True:
                success, frame = self._source.read()
                if not success or frame is None:
                    break

                for processor in self._processors:
                    frame = processor(frame)

                yield frame
        finally:
            self._source.release()
