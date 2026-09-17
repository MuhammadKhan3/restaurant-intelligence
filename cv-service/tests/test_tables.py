"""Tests for the table zone data model, store, state machine, and visualization."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from app.tables.models import TableZone
from app.tables.occupancy import (
    TableOccupancy,
    assign_people_to_tables,
    detect_table_occupancy,
    person_center_point,
    point_in_polygon,
)
from app.tables.state import StateChange, TableState, TableStateManager
from app.tables.store import TableZoneStore
from app.tables.timing import TableTimingTracker
from app.tables.visualization import draw_table_zones
from app.tracking.types import Track


def _zone(zone_id: str = "t1", capacity: int = 4) -> TableZone:
    return TableZone(
        id=zone_id,
        name="Table 1",
        capacity=capacity,
        points=[(0, 0), (10, 0), (10, 10), (0, 10)],
    )


def test_table_zone_rejects_non_positive_capacity() -> None:
    with pytest.raises(ValidationError):
        TableZone(id="t1", name="Table 1", capacity=0, points=[(0, 0), (1, 0), (1, 1)])


def test_table_zone_rejects_fewer_than_three_points() -> None:
    with pytest.raises(ValidationError):
        TableZone(id="t1", name="Table 1", capacity=4, points=[(0, 0), (1, 0)])


def test_store_create_and_get() -> None:
    store = TableZoneStore()
    store.create(_zone())

    assert store.get("t1") == _zone()


def test_store_create_rejects_duplicate_id() -> None:
    store = TableZoneStore()
    store.create(_zone())

    with pytest.raises(ValueError):
        store.create(_zone())


def test_store_list_returns_all_zones() -> None:
    store = TableZoneStore()
    store.create(_zone("t1"))
    store.create(_zone("t2"))

    assert {zone.id for zone in store.list()} == {"t1", "t2"}


def test_store_update_replaces_existing_zone() -> None:
    store = TableZoneStore()
    store.create(_zone("t1", capacity=4))

    updated = store.update("t1", _zone("t1", capacity=6))

    assert updated.capacity == 6
    assert store.get("t1").capacity == 6


def test_store_update_missing_zone_raises() -> None:
    store = TableZoneStore()

    with pytest.raises(KeyError):
        store.update("missing", _zone("missing"))


def test_store_delete_removes_zone() -> None:
    store = TableZoneStore()
    store.create(_zone())

    store.delete("t1")

    assert store.get("t1") is None


def test_store_delete_missing_zone_raises() -> None:
    store = TableZoneStore()

    with pytest.raises(KeyError):
        store.delete("missing")


def test_store_save_and_load_round_trip(tmp_path: Path) -> None:
    file_path = tmp_path / "zones.json"
    store = TableZoneStore()
    store.create(_zone("t1"))
    store.create(_zone("t2"))
    store.save(str(file_path))

    loaded_store = TableZoneStore()
    loaded_store.load(str(file_path))

    assert {zone.id for zone in loaded_store.list()} == {"t1", "t2"}
    assert loaded_store.get("t1") == _zone("t1")


def test_store_load_missing_file_results_in_empty_store(tmp_path: Path) -> None:
    store = TableZoneStore()

    store.load(str(tmp_path / "does-not-exist.json"))

    assert store.list() == []


def test_draw_table_zones_annotates_a_copy_without_mutating_original() -> None:
    frame = np.zeros((50, 50, 3), dtype=np.uint8)
    original = frame.copy()

    annotated = draw_table_zones(frame, [_zone()])

    assert annotated.shape == frame.shape
    assert not np.array_equal(annotated, frame)
    assert np.array_equal(frame, original)


def _track(track_id: int, bbox: tuple[int, int, int, int]) -> Track:
    return Track(track_id=track_id, bbox=bbox, confidence=0.9, class_id=0, class_name="person")


def test_person_center_point_returns_bbox_midpoint() -> None:
    assert person_center_point((0, 0, 10, 20)) == (5.0, 10.0)


def test_point_in_polygon_inside() -> None:
    square = [(0, 0), (10, 0), (10, 10), (0, 10)]

    assert point_in_polygon((5, 5), square) is True


def test_point_in_polygon_outside() -> None:
    square = [(0, 0), (10, 0), (10, 10), (0, 10)]

    assert point_in_polygon((15, 15), square) is False


def test_point_in_polygon_on_edge_is_inside() -> None:
    square = [(0, 0), (10, 0), (10, 10), (0, 10)]

    assert point_in_polygon((0, 5), square) is True


def test_assign_people_to_tables_assigns_by_center_point() -> None:
    zone = _zone()  # square (0,0)-(10,10)
    inside_track = _track(1, (2, 2, 4, 4))
    outside_track = _track(2, (100, 100, 110, 110))

    assignments = assign_people_to_tables([inside_track, outside_track], [zone])

    assert assignments == {"t1": [1]}


def test_assign_people_to_tables_first_matching_zone_wins_on_overlap() -> None:
    zone_a = _zone("t1")
    zone_b = TableZone(
        id="t2", name="Table 2", capacity=4, points=[(0, 0), (10, 0), (10, 10), (0, 10)]
    )
    track = _track(1, (2, 2, 4, 4))

    assignments = assign_people_to_tables([track], [zone_a, zone_b])

    assert assignments == {"t1": [1], "t2": []}


def test_detect_table_occupancy_below_threshold_is_available() -> None:
    zone = _zone()
    track = _track(1, (2, 2, 4, 4))

    results = detect_table_occupancy([track], [zone], occupancy_threshold=2)

    assert results == [TableOccupancy(zone_id="t1", person_count=1, occupied=False, track_ids=[1])]


def test_detect_table_occupancy_meets_threshold_is_occupied() -> None:
    zone = _zone()
    tracks = [_track(1, (2, 2, 4, 4)), _track(2, (5, 5, 6, 6))]

    results = detect_table_occupancy(tracks, [zone], occupancy_threshold=2)

    assert results == [
        TableOccupancy(zone_id="t1", person_count=2, occupied=True, track_ids=[1, 2])
    ]


def test_detect_table_occupancy_empty_zone_is_available() -> None:
    zone = _zone()

    results = detect_table_occupancy([], [zone])

    assert results == [TableOccupancy(zone_id="t1", person_count=0, occupied=False, track_ids=[])]


def _occupancy(zone_id: str = "t1", occupied: bool = True) -> TableOccupancy:
    return TableOccupancy(
        zone_id=zone_id, person_count=1 if occupied else 0, occupied=occupied, track_ids=[]
    )


def test_new_zone_starts_unknown() -> None:
    manager = TableStateManager()

    assert manager.current_state("t1") == TableState.UNKNOWN


def test_state_requires_consecutive_frames_before_transition() -> None:
    manager = TableStateManager(debounce_frames=3)

    manager.update([_occupancy(occupied=True)])
    manager.update([_occupancy(occupied=True)])
    assert manager.current_state("t1") == TableState.UNKNOWN

    manager.update([_occupancy(occupied=True)])
    assert manager.current_state("t1") == TableState.OCCUPIED


def test_flicker_resets_the_debounce_counter() -> None:
    manager = TableStateManager(debounce_frames=2)

    manager.update([_occupancy(occupied=True)])
    manager.update([_occupancy(occupied=False)])
    manager.update([_occupancy(occupied=True)])
    assert manager.current_state("t1") == TableState.UNKNOWN

    manager.update([_occupancy(occupied=True)])
    assert manager.current_state("t1") == TableState.OCCUPIED


def test_state_toggles_between_available_and_occupied() -> None:
    manager = TableStateManager(debounce_frames=1)

    manager.update([_occupancy(occupied=True)])
    assert manager.current_state("t1") == TableState.OCCUPIED

    manager.update([_occupancy(occupied=False)])
    assert manager.current_state("t1") == TableState.AVAILABLE


def test_manual_state_overrides_and_blocks_automatic_updates() -> None:
    manager = TableStateManager(debounce_frames=1)

    manager.set_manual_state("t1", TableState.CLEANING)
    manager.update([_occupancy(occupied=True)])

    assert manager.current_state("t1") == TableState.CLEANING


def test_set_manual_state_rejects_non_manual_states() -> None:
    manager = TableStateManager()

    with pytest.raises(ValueError):
        manager.set_manual_state("t1", TableState.AVAILABLE)


def test_clear_manual_state_returns_zone_to_unknown() -> None:
    manager = TableStateManager(debounce_frames=1)
    manager.set_manual_state("t1", TableState.BLOCKED)

    manager.clear_manual_state("t1")

    assert manager.current_state("t1") == TableState.UNKNOWN


def test_clear_manual_state_on_non_manual_zone_is_a_no_op() -> None:
    manager = TableStateManager(debounce_frames=1)
    manager.update([_occupancy(occupied=True)])

    manager.clear_manual_state("t1")

    assert manager.current_state("t1") == TableState.OCCUPIED


def test_history_records_each_confirmed_transition() -> None:
    fixed_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    manager = TableStateManager(debounce_frames=1, clock=lambda: fixed_time)

    manager.update([_occupancy(occupied=True)])
    manager.update([_occupancy(occupied=False)])

    history = manager.history("t1")
    assert [change.to_state for change in history] == [TableState.OCCUPIED, TableState.AVAILABLE]
    assert [change.from_state for change in history] == [TableState.UNKNOWN, TableState.OCCUPIED]
    assert all(change.timestamp == fixed_time for change in history)


def test_history_is_empty_for_unseen_zone() -> None:
    manager = TableStateManager()

    assert manager.history("t1") == []


def test_debounce_frames_must_be_at_least_one() -> None:
    with pytest.raises(ValueError):
        TableStateManager(debounce_frames=0)


def _change(
    zone_id: str, from_state: TableState, to_state: TableState, timestamp: datetime
) -> StateChange:
    return StateChange(zone_id=zone_id, from_state=from_state, to_state=to_state, timestamp=timestamp)


def test_occupied_transition_opens_a_session() -> None:
    start = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    tracker = TableTimingTracker()

    tracker.record_state_change(_change("t1", TableState.AVAILABLE, TableState.OCCUPIED, start))

    session = tracker.current_session("t1")
    assert session is not None
    assert session.start_time == start
    assert session.is_open


def test_leaving_occupied_closes_the_session_and_records_history() -> None:
    start = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    end = start + timedelta(minutes=45)
    tracker = TableTimingTracker()
    tracker.record_state_change(_change("t1", TableState.AVAILABLE, TableState.OCCUPIED, start))

    tracker.record_state_change(_change("t1", TableState.OCCUPIED, TableState.AVAILABLE, end))

    assert tracker.current_session("t1") is None
    history = tracker.history("t1")
    assert len(history) == 1
    assert history[0].start_time == start
    assert history[0].end_time == end
    assert history[0].duration() == timedelta(minutes=45)


def test_leaving_occupied_for_cleaning_also_closes_the_session() -> None:
    start = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    end = start + timedelta(minutes=10)
    tracker = TableTimingTracker()
    tracker.record_state_change(_change("t1", TableState.AVAILABLE, TableState.OCCUPIED, start))

    tracker.record_state_change(_change("t1", TableState.OCCUPIED, TableState.CLEANING, end))

    assert tracker.current_session("t1") is None
    assert tracker.history("t1")[0].end_time == end


def test_open_session_duration_requires_now() -> None:
    start = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    tracker = TableTimingTracker()
    tracker.record_state_change(_change("t1", TableState.AVAILABLE, TableState.OCCUPIED, start))

    with pytest.raises(ValueError):
        tracker.current_session("t1").duration()

    now = start + timedelta(minutes=5)
    assert tracker.current_session("t1").duration(now) == timedelta(minutes=5)


def test_is_long_occupancy_uses_the_injected_clock() -> None:
    start = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    now = start + timedelta(hours=2)
    tracker = TableTimingTracker(clock=lambda: now)
    tracker.record_state_change(_change("t1", TableState.AVAILABLE, TableState.OCCUPIED, start))

    assert tracker.is_long_occupancy("t1", threshold=timedelta(hours=1)) is True
    assert tracker.is_long_occupancy("t1", threshold=timedelta(hours=3)) is False


def test_is_long_occupancy_false_when_no_open_session() -> None:
    tracker = TableTimingTracker()

    assert tracker.is_long_occupancy("t1", threshold=timedelta(minutes=1)) is False


def test_timing_history_empty_for_unseen_zone() -> None:
    tracker = TableTimingTracker()

    assert tracker.history("t1") == []
