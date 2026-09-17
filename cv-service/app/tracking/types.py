"""Data types shared across the tracking module."""

from dataclasses import dataclass, field
from enum import StrEnum

from app.detection.types import BoundingBox


@dataclass(frozen=True)
class Track:
    """A single tracked person in one frame, as reported by the tracker."""

    track_id: int
    bbox: BoundingBox
    confidence: float
    class_id: int
    class_name: str


class TrackState(StrEnum):
    """Lifecycle state of a track across frames."""

    ACTIVE = "active"
    LOST = "lost"
    REMOVED = "removed"


@dataclass
class TrackRecord:
    """A track's latest known state, kept across frames by TrackLifecycleManager."""

    track_id: int
    bbox: BoundingBox
    confidence: float
    class_id: int
    class_name: str
    state: TrackState = field(default=TrackState.ACTIVE)
    frames_since_seen: int = 0
