"""Tests for the wait-time estimator: turnover averages and wait estimation."""

from datetime import datetime, timedelta, timezone

import pytest

from app.tables.models import TableZone
from app.tables.state import StateChange, TableState
from app.tables.timing import TableTimingTracker
from app.waittime.estimator import WaitTimeEstimator

START = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)


def _zone(zone_id: str, capacity: int) -> TableZone:
    return TableZone(id=zone_id, name=zone_id, capacity=capacity, points=[(0, 0), (1, 0), (1, 1)])


def _change(zone_id: str, from_state: TableState, to_state: TableState, timestamp: datetime) -> StateChange:
    return StateChange(zone_id=zone_id, from_state=from_state, to_state=to_state, timestamp=timestamp)


def test_average_turnover_uses_default_with_no_history() -> None:
    estimator = WaitTimeEstimator(TableTimingTracker(), default_turnover=timedelta(minutes=30))

    assert estimator.average_turnover("t1") == timedelta(minutes=30)


def test_average_turnover_uses_completed_session_history() -> None:
    tracker = TableTimingTracker()
    tracker.record_state_change(_change("t1", TableState.AVAILABLE, TableState.OCCUPIED, START))
    tracker.record_state_change(
        _change("t1", TableState.OCCUPIED, TableState.AVAILABLE, START + timedelta(minutes=40))
    )
    estimator = WaitTimeEstimator(tracker)

    assert estimator.average_turnover("t1") == timedelta(minutes=40)


def test_estimate_wait_is_zero_when_a_table_is_immediately_available() -> None:
    estimator = WaitTimeEstimator(TableTimingTracker())
    zones = [_zone("t1", 4)]
    states = {"t1": TableState.AVAILABLE}

    estimate = estimator.estimate_wait(2, zones, states, now=START)

    assert estimate.wait == timedelta(0)
    assert estimate.zone_id == "t1"


def test_estimate_wait_raises_when_no_table_could_ever_fit() -> None:
    estimator = WaitTimeEstimator(TableTimingTracker())
    zones = [_zone("t1", 2)]

    with pytest.raises(ValueError):
        estimator.estimate_wait(4, zones, {"t1": TableState.AVAILABLE}, now=START)


def test_estimate_wait_uses_remaining_turnover_of_an_occupied_table() -> None:
    tracker = TableTimingTracker()
    tracker.record_state_change(_change("t1", TableState.AVAILABLE, TableState.OCCUPIED, START))
    zones = [_zone("t1", 4)]
    states = {"t1": TableState.OCCUPIED}
    estimator = WaitTimeEstimator(tracker, default_turnover=timedelta(minutes=30))

    now = START + timedelta(minutes=10)
    estimate = estimator.estimate_wait(2, zones, states, now=now)

    assert estimate.zone_id == "t1"
    assert estimate.wait == timedelta(minutes=20)


def test_estimate_wait_never_goes_negative_past_average_turnover() -> None:
    tracker = TableTimingTracker()
    tracker.record_state_change(_change("t1", TableState.AVAILABLE, TableState.OCCUPIED, START))
    zones = [_zone("t1", 4)]
    states = {"t1": TableState.OCCUPIED}
    estimator = WaitTimeEstimator(tracker, default_turnover=timedelta(minutes=30))

    now = START + timedelta(hours=2)
    estimate = estimator.estimate_wait(2, zones, states, now=now)

    assert estimate.wait == timedelta(0)


def test_estimate_wait_picks_the_soonest_occupied_table() -> None:
    tracker = TableTimingTracker()
    tracker.record_state_change(_change("t1", TableState.AVAILABLE, TableState.OCCUPIED, START))
    tracker.record_state_change(
        _change("t2", TableState.AVAILABLE, TableState.OCCUPIED, START + timedelta(minutes=25))
    )
    zones = [_zone("t1", 4), _zone("t2", 4)]
    states = {"t1": TableState.OCCUPIED, "t2": TableState.OCCUPIED}
    estimator = WaitTimeEstimator(tracker, default_turnover=timedelta(minutes=30))

    now = START + timedelta(minutes=25)
    estimate = estimator.estimate_wait(2, zones, states, now=now)

    # t1 has been occupied 25 of its ~30min average turnover (5min left);
    # t2 only just became occupied (30min left) -> t1 frees up sooner.
    assert estimate.zone_id == "t1"
    assert estimate.wait == timedelta(minutes=5)


def test_estimate_wait_falls_back_to_default_when_no_table_is_occupied_or_available() -> None:
    estimator = WaitTimeEstimator(TableTimingTracker(), default_turnover=timedelta(minutes=30))
    zones = [_zone("t1", 4)]
    states = {"t1": TableState.CLEANING}

    estimate = estimator.estimate_wait(2, zones, states, now=START)

    assert estimate.zone_id is None
    assert estimate.wait == timedelta(minutes=30)
