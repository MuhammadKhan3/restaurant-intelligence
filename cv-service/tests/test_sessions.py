"""Tests for continuous table dining sessions: arrival, occlusion, departure, new groups."""

from datetime import datetime, timedelta, timezone

from app.sessions.models import SessionStatus
from app.sessions.tracker import TableSessionTracker

START = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
GRACE = timedelta(minutes=2)


def test_no_session_when_zone_has_never_had_anyone() -> None:
    tracker = TableSessionTracker(empty_grace_period=GRACE)

    assert tracker.current_session("t8") is None
    assert tracker.current_customer_count("t8") == 0


def test_arrival_starts_a_new_active_session() -> None:
    tracker = TableSessionTracker(empty_grace_period=GRACE)

    tracker.update("t8", [1, 2, 3], now=START)

    session = tracker.current_session("t8")
    assert session is not None
    assert session.is_active
    assert session.started_at == START
    assert session.track_ids == frozenset({1, 2, 3})
    assert session.peak_customer_count == 3
    assert tracker.current_customer_count("t8") == 3


def test_occluded_customer_still_present_keeps_the_same_session() -> None:
    """Spec section 3: a customer temporarily hidden and reappearing is one session.

    `TrackLifecycleManager` (Phase 4) is what keeps an occluded customer's
    track id appearing here uninterrupted (as LOST, not REMOVED) -- from this
    tracker's point of view that just looks like the same track id showing up
    on every tick, so the session never sees a gap.
    """
    tracker = TableSessionTracker(empty_grace_period=GRACE)
    tracker.update("t8", [1], now=START)

    tracker.update("t8", [1], now=START + timedelta(minutes=10, seconds=30))

    session = tracker.current_session("t8")
    assert session is not None
    assert session.is_active
    assert session.started_at == START  # unchanged -- still the same session


def test_temporarily_empty_zone_within_grace_period_keeps_session_active() -> None:
    """Everyone briefly out of frame at once -- table-level grace period covers this."""
    tracker = TableSessionTracker(empty_grace_period=GRACE)
    tracker.update("t8", [1, 2], now=START)

    tracker.update("t8", [], now=START + timedelta(seconds=30))
    tracker.update("t8", [1, 2], now=START + timedelta(seconds=45))

    session = tracker.current_session("t8")
    assert session is not None
    assert session.is_active
    assert session.started_at == START


def test_session_ends_after_empty_grace_period_elapses() -> None:
    tracker = TableSessionTracker(empty_grace_period=GRACE)
    tracker.update("t8", [1, 2, 3], now=START)

    empty_at = START + timedelta(hours=1)
    tracker.update("t8", [], now=empty_at)
    tracker.update("t8", [], now=empty_at + GRACE)

    assert tracker.current_session("t8") is None
    history = tracker.history("t8")
    assert len(history) == 1
    assert history[0].status == SessionStatus.COMPLETED
    assert history[0].ended_at == empty_at  # session end time is when it actually emptied
    assert history[0].duration() == timedelta(hours=1)


def test_session_not_yet_ended_before_grace_period_elapses() -> None:
    tracker = TableSessionTracker(empty_grace_period=GRACE)
    tracker.update("t8", [1], now=START)

    empty_at = START + timedelta(hours=1)
    tracker.update("t8", [], now=empty_at)
    tracker.update("t8", [], now=empty_at + timedelta(seconds=30))

    assert tracker.current_session("t8") is not None
    assert tracker.history("t8") == []


def test_new_group_starts_a_new_session_after_the_previous_one_ends() -> None:
    """Spec section 5: Group 1 leaves, Group 2 arrives -- two separate sessions."""
    tracker = TableSessionTracker(empty_grace_period=GRACE)
    tracker.update("t8", [1, 2, 3], now=START)
    empty_at = START + timedelta(hours=1)
    tracker.update("t8", [], now=empty_at)
    tracker.update("t8", [], now=empty_at + GRACE)

    new_group_start = START + timedelta(hours=1, minutes=10)
    tracker.update("t8", [4, 5], now=new_group_start)

    current = tracker.current_session("t8")
    assert current is not None
    assert current.track_ids == frozenset({4, 5})
    assert current.started_at == new_group_start
    assert len(tracker.history("t8")) == 1  # group 1's completed session


def test_peak_customer_count_reflects_the_largest_group_seen() -> None:
    tracker = TableSessionTracker(empty_grace_period=GRACE)
    tracker.update("t8", [1, 2], now=START)
    tracker.update("t8", [1, 2, 3, 4], now=START + timedelta(minutes=5))
    tracker.update("t8", [1, 2], now=START + timedelta(minutes=10))

    session = tracker.current_session("t8")
    assert session.peak_customer_count == 4
    assert session.track_ids == frozenset({1, 2, 3, 4})


def test_current_customer_count_drops_to_zero_during_a_grace_period_gap() -> None:
    tracker = TableSessionTracker(empty_grace_period=GRACE)
    tracker.update("t8", [1, 2], now=START)

    tracker.update("t8", [], now=START + timedelta(seconds=10))

    assert tracker.current_customer_count("t8") == 0
    assert tracker.current_session("t8").is_active


def test_history_across_multiple_tables() -> None:
    tracker = TableSessionTracker(empty_grace_period=GRACE)
    tracker.update("t1", [1], now=START)
    tracker.update("t2", [2], now=START)
    for zone in ("t1", "t2"):
        tracker.update(zone, [], now=START + timedelta(hours=1))
        tracker.update(zone, [], now=START + timedelta(hours=1) + GRACE)

    assert {s.zone_id for s in tracker.history()} == {"t1", "t2"}
    assert len(tracker.history("t1")) == 1


def test_duration_of_an_active_session_requires_now() -> None:
    tracker = TableSessionTracker(empty_grace_period=GRACE)
    tracker.update("t8", [1], now=START)

    session = tracker.current_session("t8")
    now = START + timedelta(minutes=58)
    assert session.duration(now) == timedelta(minutes=58)
