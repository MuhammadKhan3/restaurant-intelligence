"""Tests for available-table matching and the table assignment service."""

from datetime import datetime, timezone

from app.assignment.matcher import find_available_tables, match_table_for_group
from app.assignment.models import AssignmentStatus
from app.assignment.service import TableAssignmentService
from app.tables.models import TableZone
from app.tables.state import TableState


def _zone(zone_id: str, capacity: int) -> TableZone:
    return TableZone(id=zone_id, name=zone_id, capacity=capacity, points=[(0, 0), (1, 0), (1, 1)])


def test_find_available_tables_filters_by_state() -> None:
    zones = [_zone("t1", 2), _zone("t2", 4)]
    states = {"t1": TableState.OCCUPIED, "t2": TableState.AVAILABLE}

    available = find_available_tables(zones, states)

    assert [zone.id for zone in available] == ["t2"]


def test_find_available_tables_treats_unseen_zone_as_unavailable() -> None:
    zones = [_zone("t1", 2)]

    assert find_available_tables(zones, {}) == []


def test_match_table_for_group_picks_smallest_fitting_capacity() -> None:
    zones = [_zone("t1", 6), _zone("t2", 2), _zone("t3", 4)]

    match = match_table_for_group(2, zones)

    assert match is not None
    assert match.id == "t2"


def test_match_table_for_group_returns_none_when_nothing_fits() -> None:
    zones = [_zone("t1", 2)]

    assert match_table_for_group(4, zones) is None


def test_assign_matches_the_smallest_fitting_available_table() -> None:
    fixed_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    service = TableAssignmentService(clock=lambda: fixed_time)
    zones = [_zone("t1", 6), _zone("t2", 2)]
    states = {"t1": TableState.AVAILABLE, "t2": TableState.AVAILABLE}

    assignment = service.assign([101, 102], zones, states)

    assert assignment is not None
    assert assignment.zone_id == "t2"
    assert assignment.track_ids == [101, 102]
    assert assignment.assigned_at == fixed_time
    assert assignment.status == AssignmentStatus.WALKING
    assert service.current_assignment("t2") == assignment


def test_assign_returns_none_when_no_table_fits() -> None:
    service = TableAssignmentService()
    zones = [_zone("t1", 2)]
    states = {"t1": TableState.AVAILABLE}

    assert service.assign([1, 2, 3], zones, states) is None


def test_assign_excludes_tables_already_assigned() -> None:
    service = TableAssignmentService()
    zones = [_zone("t1", 4)]
    states = {"t1": TableState.AVAILABLE}
    service.assign([1], zones, states)

    assert service.assign([2], zones, states) is None


def test_confirm_seated_transitions_walking_to_seated() -> None:
    service = TableAssignmentService()
    zones = [_zone("t1", 4)]
    states = {"t1": TableState.AVAILABLE}
    service.assign([1], zones, states)

    confirmed = service.confirm_seated("t1")

    assert confirmed is not None
    assert confirmed.status == AssignmentStatus.SEATED
    assert confirmed.seated_at is not None


def test_confirm_seated_on_unknown_zone_is_a_no_op() -> None:
    service = TableAssignmentService()

    assert service.confirm_seated("missing") is None


def test_confirm_seated_twice_is_a_no_op_the_second_time() -> None:
    service = TableAssignmentService()
    zones = [_zone("t1", 4)]
    states = {"t1": TableState.AVAILABLE}
    service.assign([1], zones, states)
    service.confirm_seated("t1")

    assert service.confirm_seated("t1") is None


def test_release_frees_the_table_and_records_history() -> None:
    service = TableAssignmentService()
    zones = [_zone("t1", 4)]
    states = {"t1": TableState.AVAILABLE}
    service.assign([1], zones, states)

    released = service.release("t1")

    assert released is not None
    assert service.current_assignment("t1") is None
    assert service.history() == [released]
    assert service.assign([2], zones, states) is not None
