"""Tests for the entrance zone model, entry/exit tracker, and customer counter."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.entrance.counter import CustomerCounter
from app.entrance.models import EntranceZone
from app.entrance.tracker import EntranceEvent, EntranceEventType, EntranceTracker
from app.tracking.types import Track


def _zone() -> EntranceZone:
    return EntranceZone(
        id="main",
        name="Main Entrance",
        outside_points=[(0, 0), (10, 0), (10, 10), (0, 10)],
        inside_points=[(20, 0), (30, 0), (30, 10), (20, 10)],
    )


def _track(track_id: int, center: tuple[int, int]) -> Track:
    x, y = center
    return Track(track_id=track_id, bbox=(x, y, x, y), confidence=0.9, class_id=0, class_name="person")


OUTSIDE = (5, 5)
INSIDE = (25, 5)
NEITHER = (100, 100)


def test_entrance_zone_rejects_fewer_than_three_points() -> None:
    with pytest.raises(ValidationError):
        EntranceZone(
            id="main", name="Main", outside_points=[(0, 0), (1, 0)], inside_points=[(2, 0), (3, 0), (3, 1)]
        )


def test_first_sighting_emits_no_event() -> None:
    tracker = EntranceTracker(_zone())

    events = tracker.update([_track(1, OUTSIDE)])

    assert events == []


def test_outside_to_inside_is_an_entry() -> None:
    tracker = EntranceTracker(_zone())
    tracker.update([_track(1, OUTSIDE)])

    events = tracker.update([_track(1, INSIDE)])

    assert len(events) == 1
    assert events[0].zone_id == "main"
    assert events[0].track_id == 1
    assert events[0].event_type == EntranceEventType.ENTRY


def test_inside_to_outside_is_an_exit() -> None:
    tracker = EntranceTracker(_zone())
    tracker.update([_track(1, INSIDE)])

    events = tracker.update([_track(1, OUTSIDE)])

    assert len(events) == 1
    assert events[0].event_type == EntranceEventType.EXIT


def test_staying_on_the_same_side_emits_no_event() -> None:
    tracker = EntranceTracker(_zone())
    tracker.update([_track(1, OUTSIDE)])

    events = tracker.update([_track(1, OUTSIDE)])

    assert events == []


def test_leaving_both_zones_does_not_reset_the_last_known_side() -> None:
    tracker = EntranceTracker(_zone())
    tracker.update([_track(1, OUTSIDE)])

    assert tracker.update([_track(1, NEITHER)]) == []

    events = tracker.update([_track(1, INSIDE)])
    assert len(events) == 1
    assert events[0].event_type == EntranceEventType.ENTRY


def test_uses_the_injected_clock_for_event_timestamps() -> None:
    fixed_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    tracker = EntranceTracker(_zone(), clock=lambda: fixed_time)
    tracker.update([_track(1, OUTSIDE)])

    events = tracker.update([_track(1, INSIDE)])

    assert events[0].timestamp == fixed_time


def _event(event_type: EntranceEventType) -> EntranceEvent:
    return EntranceEvent(
        zone_id="main", track_id=1, event_type=event_type, timestamp=datetime.now(timezone.utc)
    )


def test_counter_increments_on_entry() -> None:
    counter = CustomerCounter()

    count = counter.apply([_event(EntranceEventType.ENTRY)])

    assert count == 1
    assert counter.current_count == 1


def test_counter_decrements_on_exit() -> None:
    counter = CustomerCounter()
    counter.apply([_event(EntranceEventType.ENTRY), _event(EntranceEventType.ENTRY)])

    count = counter.apply([_event(EntranceEventType.EXIT)])

    assert count == 1


def test_counter_does_not_go_negative() -> None:
    counter = CustomerCounter()

    count = counter.apply([_event(EntranceEventType.EXIT)])

    assert count == 0
