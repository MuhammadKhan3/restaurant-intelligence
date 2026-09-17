"""Video source interface and connection status."""

from abc import ABC, abstractmethod
from enum import StrEnum

import numpy as np


class ConnectionStatus(StrEnum):
    """Connection state of a video source."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class VideoSource(ABC):
    """Common interface for any source that can produce video frames."""

    def __init__(self) -> None:
        self._status = ConnectionStatus.DISCONNECTED

    @property
    def status(self) -> ConnectionStatus:
        return self._status

    @property
    def is_connected(self) -> bool:
        return self._status == ConnectionStatus.CONNECTED

    @abstractmethod
    def connect(self) -> None:
        """Open the underlying video source."""

    @abstractmethod
    def read(self) -> tuple[bool, np.ndarray | None]:
        """Read the next frame. Returns (success, frame)."""

    @abstractmethod
    def release(self) -> None:
        """Release the underlying video source."""
