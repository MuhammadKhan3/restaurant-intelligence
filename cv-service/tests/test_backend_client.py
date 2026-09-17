"""Tests for the backend event-forwarding client."""

import json
from collections.abc import Callable
from datetime import datetime, timezone

import httpx

from app.entrance.tracker import EntranceEvent, EntranceEventType
from app.queue.tracker import QueueEvent, QueueEventType
from app.services.backend_client import BackendEventForwarder
from app.tables.state import StateChange, TableState


def _forwarder(handler: Callable[[httpx.Request], httpx.Response]) -> BackendEventForwarder:
    client = httpx.Client(base_url="http://backend.test", transport=httpx.MockTransport(handler))
    return BackendEventForwarder("http://backend.test", client=client)


def test_send_table_state_change_posts_expected_payload() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(201, json={})

    forwarder = _forwarder(handler)
    change = StateChange(
        zone_id="t1",
        from_state=TableState.AVAILABLE,
        to_state=TableState.OCCUPIED,
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )

    forwarder.send_table_state_change(change)

    assert len(requests) == 1
    assert requests[0].url.path == "/events/tables"
    assert json.loads(requests[0].content) == {
        "zone_id": "t1",
        "from_state": "available",
        "to_state": "occupied",
        "occurred_at": "2024-01-01T00:00:00+00:00",
    }


def test_send_camera_status_posts_expected_payload() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(201, json={})

    forwarder = _forwarder(handler)

    forwarder.send_camera_status("cam1", "connected", datetime(2024, 1, 1, tzinfo=timezone.utc))

    assert len(requests) == 1
    assert requests[0].url.path == "/events/cameras"
    assert json.loads(requests[0].content) == {
        "camera_id": "cam1",
        "status": "connected",
        "occurred_at": "2024-01-01T00:00:00+00:00",
    }


def test_send_entrance_event_posts_expected_payload() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(201, json={})

    forwarder = _forwarder(handler)
    event = EntranceEvent(
        zone_id="main",
        track_id=7,
        event_type=EntranceEventType.ENTRY,
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )

    forwarder.send_entrance_event(event)

    assert len(requests) == 1
    assert requests[0].url.path == "/events/entrance"
    assert json.loads(requests[0].content) == {
        "zone_id": "main",
        "track_id": 7,
        "event_type": "entry",
        "occurred_at": "2024-01-01T00:00:00+00:00",
    }


def test_send_queue_event_posts_expected_payload() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(201, json={})

    forwarder = _forwarder(handler)
    event = QueueEvent(
        zone_id="queue1",
        track_id=3,
        event_type=QueueEventType.ENTRY,
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )

    forwarder.send_queue_event(event)

    assert len(requests) == 1
    assert requests[0].url.path == "/events/queue"
    assert json.loads(requests[0].content) == {
        "zone_id": "queue1",
        "track_id": 3,
        "event_type": "entry",
        "occurred_at": "2024-01-01T00:00:00+00:00",
    }


def test_forwarding_failure_is_logged_not_raised() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    forwarder = _forwarder(handler)
    change = StateChange(
        zone_id="t1",
        from_state=TableState.UNKNOWN,
        to_state=TableState.AVAILABLE,
        timestamp=datetime.now(timezone.utc),
    )

    forwarder.send_table_state_change(change)


def test_connection_error_is_logged_not_raised() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    forwarder = _forwarder(handler)
    change = StateChange(
        zone_id="t1",
        from_state=TableState.UNKNOWN,
        to_state=TableState.AVAILABLE,
        timestamp=datetime.now(timezone.utc),
    )

    forwarder.send_table_state_change(change)
