"""Stores raised alerts, dedupes active ones, and handles acknowledgement."""

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime

from app.alerts.models import Alert, AlertType
from app.tables.state import utc_now

Clock = Callable[[], datetime]


class AlertManager:
    """Keeps at most one active (unacknowledged) alert per (type, subject).

    `active_alerts()` is the data an "Alert Dashboard" would render.
    """

    def __init__(self, clock: Clock = utc_now) -> None:
        self._clock = clock
        self._active: dict[tuple[AlertType, str], Alert] = {}
        self._history: list[Alert] = []
        self._next_id = 1

    def raise_alert(self, alert: Alert) -> Alert | None:
        """Register a detected alert. None if one of the same type+subject is
        already active, so a persistent condition doesn't spam duplicates.
        """
        key = (alert.alert_type, alert.subject_id)
        if key in self._active:
            return None

        stored = replace(alert, id=str(self._next_id))
        self._next_id += 1
        self._active[key] = stored
        self._history.append(stored)
        return stored

    def acknowledge(self, alert_id: str) -> Alert | None:
        for key, alert in list(self._active.items()):
            if alert.id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_at = self._clock()
                del self._active[key]
                return alert
        return None

    def active_alerts(self) -> list[Alert]:
        return list(self._active.values())

    def history(self) -> list[Alert]:
        return list(self._history)
