"""Tracker interface."""

from abc import ABC, abstractmethod

import numpy as np

from app.tracking.types import Track


class Tracker(ABC):
    """Common interface for anything that tracks people across frames."""

    @abstractmethod
    def update(self, frame: np.ndarray) -> list[Track]:
        """Run tracking on a frame and return the currently tracked people."""

    @abstractmethod
    def reset(self) -> None:
        """Clear internal tracker state, e.g. after switching video sources."""
