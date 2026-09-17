"""Tracks each person's lifecycle (active / lost / removed) across frames."""

from app.tracking.types import Track, TrackRecord, TrackState


class TrackLifecycleManager:
    """Keeps track records alive across brief detection gaps.

    A track becomes LOST when it isn't reported in an update() call, and is
    dropped entirely once it has been lost for more than `max_lost_frames`
    consecutive updates.
    """

    def __init__(self, max_lost_frames: int = 30) -> None:
        self._max_lost_frames = max_lost_frames
        self._tracks: dict[int, TrackRecord] = {}

    def update(self, tracks: list[Track]) -> list[TrackRecord]:
        seen_ids = set()

        for track in tracks:
            seen_ids.add(track.track_id)
            self._tracks[track.track_id] = TrackRecord(
                track_id=track.track_id,
                bbox=track.bbox,
                confidence=track.confidence,
                class_id=track.class_id,
                class_name=track.class_name,
                state=TrackState.ACTIVE,
                frames_since_seen=0,
            )

        for track_id, record in self._tracks.items():
            if track_id in seen_ids:
                continue
            record.frames_since_seen += 1
            record.state = (
                TrackState.REMOVED
                if record.frames_since_seen > self._max_lost_frames
                else TrackState.LOST
            )

        self._tracks = {
            track_id: record
            for track_id, record in self._tracks.items()
            if record.state != TrackState.REMOVED
        }

        return list(self._tracks.values())

    def active_tracks(self) -> list[TrackRecord]:
        return [record for record in self._tracks.values() if record.state == TrackState.ACTIVE]

    def reset(self) -> None:
        self._tracks = {}
