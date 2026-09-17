"""Forwards CV-detected table/camera/entrance/queue events to the backend event API."""

import logging
from datetime import datetime

import httpx

from app.entrance.tracker import EntranceEvent
from app.queue.tracker import QueueEvent
from app.tables.state import StateChange

logger = logging.getLogger(__name__)


class BackendEventForwarder:
    """POSTs events to `backend`'s ingestion API.

    A forwarding failure (backend down, network error, non-2xx response) is
    logged and swallowed rather than raised, so a CV processing loop never
    crashes because the backend is temporarily unreachable.
    """

    def __init__(
        self, backend_url: str, timeout: float = 5.0, client: httpx.Client | None = None
    ) -> None:
        self._client = client or httpx.Client(base_url=backend_url, timeout=timeout)

    def send_table_state_change(self, change: StateChange) -> None:
        self._post(
            "/events/tables",
            {
                "zone_id": change.zone_id,
                "from_state": change.from_state.value,
                "to_state": change.to_state.value,
                "occurred_at": change.timestamp.isoformat(),
            },
        )

    def send_camera_status(self, camera_id: str, status: str, occurred_at: datetime) -> None:
        self._post(
            "/events/cameras",
            {
                "camera_id": camera_id,
                "status": status,
                "occurred_at": occurred_at.isoformat(),
            },
        )

    def send_entrance_event(self, event: EntranceEvent) -> None:
        self._post(
            "/events/entrance",
            {
                "zone_id": event.zone_id,
                "track_id": event.track_id,
                "event_type": event.event_type.value,
                "occurred_at": event.timestamp.isoformat(),
            },
        )

    def send_queue_event(self, event: QueueEvent) -> None:
        self._post(
            "/events/queue",
            {
                "zone_id": event.zone_id,
                "track_id": event.track_id,
                "event_type": event.event_type.value,
                "occurred_at": event.timestamp.isoformat(),
            },
        )

    def _post(self, path: str, payload: dict) -> None:
        try:
            response = self._client.post(path, json=payload)
            response.raise_for_status()
        except httpx.HTTPError as error:
            logger.warning("Failed to forward event to backend %s: %s", path, error)

    def close(self) -> None:
        self._client.close()
