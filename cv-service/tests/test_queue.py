"""Tests for the queue zone model, entry/exit tracker, and group estimation."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.queue.grouping import estimate_groups
from app.queue.models import QueueZone
from app.queue.tracker import QueueEventType, QueueTracker
from app.tracking.types import Track


def _zone() -> QueueZone:
    return QueueZone(id="queue1", name="Front Queue", points=[(0, 0), (100, 0), (100, 100), (0, 100)])


def _track(track_id: int, center: tuple[int, int]) -> Track:
    x, y = center
    return Track(track_id=track_id, bbox=(x, y, x, y), confidence=0.9, class_id=0, class_name="person")


INSIDE = (10, 10)
OUTSIDE = (200, 200)


def test_queue_zone_rejects_fewer_than_three_points() -> None:
    with pytest.raises(ValidationError):
        QueueZone(id="queue1", name="Queue", points=[(0, 0), (1, 0)])


def test_entering_the_zone_is_an_entry_and_counts_as_waiting() -> None:
    tracker = QueueTracker(_zone())

    events = tracker.update([_track(1, INSIDE)])

    assert len(events) == 1
    assert events[0].zone_id == "queue1"
    assert events[0].track_id == 1
    assert events[0].event_type == QueueEventType.ENTRY
    assert tracker.current_count == 1


def test_staying_in_the_zone_emits_no_further_events() -> None:
    tracker = QueueTracker(_zone())
    tracker.update([_track(1, INSIDE)])

    events = tracker.update([_track(1, INSIDE)])

    assert events == []
    assert tracker.current_count == 1


def test_leaving_the_zone_is_an_exit_and_decrements_the_count() -> None:
    tracker = QueueTracker(_zone())
    tracker.update([_track(1, INSIDE)])

    events = tracker.update([_track(1, OUTSIDE)])

    assert len(events) == 1
    assert events[0].event_type == QueueEventType.EXIT
    assert tracker.current_count == 0


def test_never_entering_the_zone_emits_nothing() -> None:
    tracker = QueueTracker(_zone())

    events = tracker.update([_track(1, OUTSIDE)])

    assert events == []
    assert tracker.current_count == 0


def test_remove_track_forces_an_exit_for_a_lost_track() -> None:
    tracker = QueueTracker(_zone())
    tracker.update([_track(1, INSIDE)])

    event = tracker.remove_track(1)

    assert event is not None
    assert event.event_type == QueueEventType.EXIT
    assert tracker.current_count == 0


def test_remove_track_on_untracked_id_is_a_no_op() -> None:
    tracker = QueueTracker(_zone())

    assert tracker.remove_track(999) is None


def test_uses_the_injected_clock_for_event_timestamps() -> None:
    fixed_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    tracker = QueueTracker(_zone(), clock=lambda: fixed_time)

    events = tracker.update([_track(1, INSIDE)])

    assert events[0].timestamp == fixed_time


def test_estimate_groups_clusters_nearby_people() -> None:
    tracks = [_track(1, (0, 0)), _track(2, (5, 0)), _track(3, (100, 100))]

    groups = estimate_groups(tracks, max_distance=10)

    group_sets = {frozenset(group) for group in groups}
    assert group_sets == {frozenset({1, 2}), frozenset({3})}


def test_estimate_groups_is_transitive() -> None:
    tracks = [_track(1, (0, 0)), _track(2, (8, 0)), _track(3, (16, 0))]

    groups = estimate_groups(tracks, max_distance=10)

    assert len(groups) == 1
    assert set(groups[0]) == {1, 2, 3}


def test_estimate_groups_empty_input() -> None:
    assert estimate_groups([], max_distance=10) == []


def test_estimate_groups_single_person_is_its_own_group() -> None:
    groups = estimate_groups([_track(1, (0, 0))], max_distance=10)

    assert groups == [[1]]
