"""Tests for queue wait timing: duration, average/max wait, abandoned waits."""

from datetime import datetime, timedelta, timezone

import pytest

from app.queue.timing import QueueTimingTracker
from app.queue.tracker import QueueEvent, QueueEventType


def _event(
    zone_id: str, track_id: int, event_type: QueueEventType, timestamp: datetime
) -> QueueEvent:
    return QueueEvent(zone_id=zone_id, track_id=track_id, event_type=event_type, timestamp=timestamp)


START = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)


def test_entry_opens_a_wait() -> None:
    tracker = QueueTimingTracker()

    tracker.record_event(_event("queue1", 1, QueueEventType.ENTRY, START))

    wait = tracker.current_wait(1)
    assert wait is not None
    assert wait.entry_time == START
    assert wait.is_open


def test_exit_closes_the_wait_and_records_history() -> None:
    end = START + timedelta(minutes=12)
    tracker = QueueTimingTracker()
    tracker.record_event(_event("queue1", 1, QueueEventType.ENTRY, START))

    tracker.record_event(_event("queue1", 1, QueueEventType.EXIT, end))

    assert tracker.current_wait(1) is None
    history = tracker.history()
    assert len(history) == 1
    assert history[0].duration() == timedelta(minutes=12)


def test_exit_with_no_matching_entry_is_a_no_op() -> None:
    tracker = QueueTimingTracker()

    tracker.record_event(_event("queue1", 1, QueueEventType.EXIT, START))

    assert tracker.history() == []


def test_open_wait_duration_requires_now() -> None:
    tracker = QueueTimingTracker()
    tracker.record_event(_event("queue1", 1, QueueEventType.ENTRY, START))

    with pytest.raises(ValueError):
        tracker.current_wait(1).duration()

    now = START + timedelta(minutes=3)
    assert tracker.current_wait(1).duration(now) == timedelta(minutes=3)


def test_average_waiting_time_across_completed_waits() -> None:
    tracker = QueueTimingTracker()
    tracker.record_event(_event("queue1", 1, QueueEventType.ENTRY, START))
    tracker.record_event(_event("queue1", 1, QueueEventType.EXIT, START + timedelta(minutes=10)))
    tracker.record_event(_event("queue1", 2, QueueEventType.ENTRY, START))
    tracker.record_event(_event("queue1", 2, QueueEventType.EXIT, START + timedelta(minutes=20)))

    assert tracker.average_waiting_time() == timedelta(minutes=15)


def test_average_waiting_time_is_none_with_no_history() -> None:
    tracker = QueueTimingTracker()

    assert tracker.average_waiting_time() is None


def test_maximum_waiting_time_across_completed_waits() -> None:
    tracker = QueueTimingTracker()
    tracker.record_event(_event("queue1", 1, QueueEventType.ENTRY, START))
    tracker.record_event(_event("queue1", 1, QueueEventType.EXIT, START + timedelta(minutes=10)))
    tracker.record_event(_event("queue1", 2, QueueEventType.ENTRY, START))
    tracker.record_event(_event("queue1", 2, QueueEventType.EXIT, START + timedelta(minutes=20)))

    assert tracker.maximum_waiting_time() == timedelta(minutes=20)


def test_maximum_waiting_time_is_none_with_no_history() -> None:
    tracker = QueueTimingTracker()

    assert tracker.maximum_waiting_time() is None


def test_history_and_averages_filter_by_zone_id() -> None:
    tracker = QueueTimingTracker()
    tracker.record_event(_event("queue1", 1, QueueEventType.ENTRY, START))
    tracker.record_event(_event("queue1", 1, QueueEventType.EXIT, START + timedelta(minutes=5)))
    tracker.record_event(_event("queue2", 2, QueueEventType.ENTRY, START))
    tracker.record_event(_event("queue2", 2, QueueEventType.EXIT, START + timedelta(minutes=30)))

    assert tracker.average_waiting_time(zone_id="queue1") == timedelta(minutes=5)
    assert tracker.maximum_waiting_time(zone_id="queue2") == timedelta(minutes=30)
    assert len(tracker.history(zone_id="queue1")) == 1


def test_abandoned_waits_returns_completed_waits_over_threshold() -> None:
    tracker = QueueTimingTracker()
    tracker.record_event(_event("queue1", 1, QueueEventType.ENTRY, START))
    tracker.record_event(_event("queue1", 1, QueueEventType.EXIT, START + timedelta(minutes=5)))
    tracker.record_event(_event("queue1", 2, QueueEventType.ENTRY, START))
    tracker.record_event(_event("queue1", 2, QueueEventType.EXIT, START + timedelta(minutes=25)))

    abandoned = tracker.abandoned_waits(threshold=timedelta(minutes=15))

    assert len(abandoned) == 1
    assert abandoned[0].track_id == 2


def test_reentering_the_queue_after_exit_opens_a_new_wait() -> None:
    tracker = QueueTimingTracker()
    tracker.record_event(_event("queue1", 1, QueueEventType.ENTRY, START))
    tracker.record_event(_event("queue1", 1, QueueEventType.EXIT, START + timedelta(minutes=5)))

    second_entry = START + timedelta(minutes=30)
    tracker.record_event(_event("queue1", 1, QueueEventType.ENTRY, second_entry))

    wait = tracker.current_wait(1)
    assert wait is not None
    assert wait.entry_time == second_entry
    assert len(tracker.history()) == 1
