"""Tests for alert detectors and the alert manager (dashboard state + acknowledgement)."""

from datetime import datetime, timedelta, timezone

from app.alerts.detectors import (
    detect_camera_offline_alert,
    detect_long_occupancy_alert,
    detect_long_queue_alert,
    detect_long_wait_alert,
    detect_unknown_table_alert,
)
from app.alerts.manager import AlertManager
from app.alerts.models import AlertType
from app.camera.base import ConnectionStatus
from app.tables.state import StateChange, TableState
from app.tables.timing import TableTimingTracker

NOW = datetime(2024, 1, 1, tzinfo=timezone.utc)


def test_detect_long_queue_alert_fires_over_threshold() -> None:
    alert = detect_long_queue_alert("queue1", waiting_count=10, threshold=5, now=NOW)

    assert alert is not None
    assert alert.alert_type == AlertType.LONG_QUEUE
    assert alert.subject_id == "queue1"


def test_detect_long_queue_alert_silent_at_or_under_threshold() -> None:
    assert detect_long_queue_alert("queue1", waiting_count=5, threshold=5, now=NOW) is None


def test_detect_long_wait_alert_fires_over_threshold() -> None:
    alert = detect_long_wait_alert(
        "queue1", wait_duration=timedelta(minutes=20), threshold=timedelta(minutes=15), now=NOW
    )

    assert alert is not None
    assert alert.alert_type == AlertType.LONG_WAIT


def test_detect_long_wait_alert_silent_under_threshold() -> None:
    alert = detect_long_wait_alert(
        "queue1", wait_duration=timedelta(minutes=5), threshold=timedelta(minutes=15), now=NOW
    )

    assert alert is None


def test_detect_long_occupancy_alert_fires_when_tracker_flags_it() -> None:
    tracker = TableTimingTracker()
    tracker.record_state_change(
        StateChange(zone_id="t1", from_state=TableState.AVAILABLE, to_state=TableState.OCCUPIED, timestamp=NOW)
    )
    later = NOW + timedelta(hours=2)

    alert = detect_long_occupancy_alert("t1", tracker, threshold=timedelta(hours=1), now=later)

    assert alert is not None
    assert alert.alert_type == AlertType.LONG_OCCUPANCY
    assert "2:00:00" in alert.message


def test_detect_long_occupancy_alert_silent_when_not_occupied() -> None:
    tracker = TableTimingTracker()

    assert detect_long_occupancy_alert("t1", tracker, threshold=timedelta(hours=1), now=NOW) is None


def test_detect_camera_offline_alert_fires_for_disconnected_or_error() -> None:
    assert detect_camera_offline_alert("cam1", ConnectionStatus.DISCONNECTED, NOW) is not None
    assert detect_camera_offline_alert("cam1", ConnectionStatus.ERROR, NOW) is not None


def test_detect_camera_offline_alert_silent_when_connected() -> None:
    assert detect_camera_offline_alert("cam1", ConnectionStatus.CONNECTED, NOW) is None


def test_detect_unknown_table_alert_fires_for_unknown_state() -> None:
    alert = detect_unknown_table_alert("t1", TableState.UNKNOWN, NOW)

    assert alert is not None
    assert alert.alert_type == AlertType.UNKNOWN_TABLE


def test_detect_unknown_table_alert_silent_for_known_state() -> None:
    assert detect_unknown_table_alert("t1", TableState.AVAILABLE, NOW) is None


def test_raise_alert_assigns_an_id_and_appears_on_the_dashboard() -> None:
    manager = AlertManager()
    draft = detect_long_queue_alert("queue1", waiting_count=10, threshold=5, now=NOW)

    stored = manager.raise_alert(draft)

    assert stored is not None
    assert stored.id != ""
    assert manager.active_alerts() == [stored]


def test_raise_alert_dedupes_same_type_and_subject() -> None:
    manager = AlertManager()
    draft = detect_long_queue_alert("queue1", waiting_count=10, threshold=5, now=NOW)
    manager.raise_alert(draft)

    duplicate = manager.raise_alert(draft)

    assert duplicate is None
    assert len(manager.active_alerts()) == 1


def test_raise_alert_allows_different_subjects_concurrently() -> None:
    manager = AlertManager()
    manager.raise_alert(detect_long_queue_alert("queue1", waiting_count=10, threshold=5, now=NOW))
    manager.raise_alert(detect_long_queue_alert("queue2", waiting_count=10, threshold=5, now=NOW))

    assert len(manager.active_alerts()) == 2


def test_acknowledge_removes_it_from_the_dashboard() -> None:
    fixed_time = NOW + timedelta(minutes=5)
    manager = AlertManager(clock=lambda: fixed_time)
    stored = manager.raise_alert(
        detect_long_queue_alert("queue1", waiting_count=10, threshold=5, now=NOW)
    )

    acknowledged = manager.acknowledge(stored.id)

    assert acknowledged.acknowledged is True
    assert acknowledged.acknowledged_at == fixed_time
    assert manager.active_alerts() == []
    assert manager.history() == [acknowledged]


def test_acknowledge_unknown_id_is_a_no_op() -> None:
    manager = AlertManager()

    assert manager.acknowledge("missing") is None
