"""Pure threshold checks that produce a draft `Alert` (empty `id`) or None.

Each detector's `Alert` has `id=""` — `AlertManager.raise_alert()` assigns the
real id (and dedupes) once the alert is actually registered.
"""

from datetime import datetime, timedelta

from app.alerts.models import Alert, AlertType
from app.camera.base import ConnectionStatus
from app.tables.state import TableState
from app.tables.timing import TableTimingTracker


def detect_long_queue_alert(zone_id: str, waiting_count: int, threshold: int, now: datetime) -> Alert | None:
    if waiting_count <= threshold:
        return None
    return Alert(
        id="",
        alert_type=AlertType.LONG_QUEUE,
        subject_id=zone_id,
        message=f"{waiting_count} people waiting in queue {zone_id} (threshold {threshold})",
        raised_at=now,
    )


def detect_long_wait_alert(
    zone_id: str, wait_duration: timedelta, threshold: timedelta, now: datetime
) -> Alert | None:
    if wait_duration <= threshold:
        return None
    return Alert(
        id="",
        alert_type=AlertType.LONG_WAIT,
        subject_id=zone_id,
        message=f"Customer has waited {wait_duration} in queue {zone_id} (threshold {threshold})",
        raised_at=now,
    )


def detect_long_occupancy_alert(
    zone_id: str, timing_tracker: TableTimingTracker, threshold: timedelta, now: datetime
) -> Alert | None:
    if not timing_tracker.is_long_occupancy(zone_id, threshold):
        return None
    session = timing_tracker.current_session(zone_id)
    duration = session.duration(now) if session is not None else threshold
    return Alert(
        id="",
        alert_type=AlertType.LONG_OCCUPANCY,
        subject_id=zone_id,
        message=f"Table {zone_id} has been occupied for {duration} (threshold {threshold})",
        raised_at=now,
    )


def detect_camera_offline_alert(camera_id: str, status: ConnectionStatus, now: datetime) -> Alert | None:
    if status not in (ConnectionStatus.DISCONNECTED, ConnectionStatus.ERROR):
        return None
    return Alert(
        id="",
        alert_type=AlertType.CAMERA_OFFLINE,
        subject_id=camera_id,
        message=f"Camera {camera_id} is {status.value}",
        raised_at=now,
    )


def detect_unknown_table_alert(zone_id: str, state: TableState, now: datetime) -> Alert | None:
    if state != TableState.UNKNOWN:
        return None
    return Alert(
        id="",
        alert_type=AlertType.UNKNOWN_TABLE,
        subject_id=zone_id,
        message=f"Table {zone_id} state is unknown",
        raised_at=now,
    )
