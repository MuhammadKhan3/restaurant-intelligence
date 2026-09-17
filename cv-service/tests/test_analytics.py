"""Tests for table session analytics: averages, turnover, utilization, peaks, buckets."""

from datetime import datetime, timedelta, timezone

from app.analytics.table_analytics import analyze_table, daily_metrics, hourly_metrics, peak_occupancy
from app.tables.timing import TableSession

START = datetime(2024, 1, 1, tzinfo=timezone.utc)


def _session(zone_id: str, start: datetime, end: datetime | None) -> TableSession:
    return TableSession(zone_id=zone_id, start_time=start, end_time=end)


def test_analyze_table_with_no_sessions_is_all_zero() -> None:
    result = analyze_table("t1", [], period=timedelta(days=1))

    assert result.session_count == 0
    assert result.average_duration == timedelta(0)
    assert result.total_duration == timedelta(0)
    assert result.turnover_per_day == 0.0
    assert result.utilization == 0.0


def test_analyze_table_ignores_other_zones_and_open_sessions() -> None:
    sessions = [
        _session("t1", START, START + timedelta(hours=1)),
        _session("t2", START, START + timedelta(hours=5)),
        _session("t1", START + timedelta(hours=2), None),
    ]

    result = analyze_table("t1", sessions, period=timedelta(days=1))

    assert result.session_count == 1
    assert result.total_duration == timedelta(hours=1)


def test_analyze_table_computes_average_and_total_duration() -> None:
    sessions = [
        _session("t1", START, START + timedelta(hours=1)),
        _session("t1", START + timedelta(hours=2), START + timedelta(hours=3)),
    ]

    result = analyze_table("t1", sessions, period=timedelta(days=1))

    assert result.total_duration == timedelta(hours=2)
    assert result.average_duration == timedelta(hours=1)


def test_analyze_table_computes_turnover_per_day() -> None:
    sessions = [_session("t1", START, START + timedelta(hours=1)) for _ in range(6)]

    result = analyze_table("t1", sessions, period=timedelta(days=2))

    assert result.turnover_per_day == 3.0


def test_analyze_table_computes_utilization() -> None:
    sessions = [_session("t1", START, START + timedelta(hours=12))]

    result = analyze_table("t1", sessions, period=timedelta(hours=24))

    assert result.utilization == 0.5


def test_analyze_table_utilization_caps_at_one() -> None:
    sessions = [
        _session("t1", START, START + timedelta(hours=20)),
        _session("t1", START + timedelta(hours=20), START + timedelta(hours=30)),
    ]

    result = analyze_table("t1", sessions, period=timedelta(hours=24))

    assert result.utilization == 1.0


def test_peak_occupancy_counts_maximum_simultaneous_sessions() -> None:
    sessions = [
        _session("t1", START, START + timedelta(hours=2)),
        _session("t2", START + timedelta(hours=1), START + timedelta(hours=3)),
        _session("t3", START + timedelta(hours=5), START + timedelta(hours=6)),
    ]

    assert peak_occupancy(sessions) == 2


def test_peak_occupancy_ignores_open_sessions() -> None:
    sessions = [_session("t1", START, None)]

    assert peak_occupancy(sessions) == 0


def test_peak_occupancy_with_no_sessions_is_zero() -> None:
    assert peak_occupancy([]) == 0


def test_hourly_metrics_splits_a_session_across_bucket_boundaries() -> None:
    sessions = [_session("t1", START + timedelta(minutes=30), START + timedelta(hours=1, minutes=30))]

    metrics = hourly_metrics("t1", sessions, START, START + timedelta(hours=2))

    assert len(metrics) == 2
    assert metrics[0].occupied_duration == timedelta(minutes=30)
    assert metrics[0].utilization == 0.5
    assert metrics[1].occupied_duration == timedelta(minutes=30)
    assert metrics[1].session_count == 1


def test_hourly_metrics_bucket_with_no_overlap_is_zero() -> None:
    sessions = [_session("t1", START, START + timedelta(minutes=10))]

    metrics = hourly_metrics("t1", sessions, START, START + timedelta(hours=2))

    assert metrics[1].occupied_duration == timedelta(0)
    assert metrics[1].session_count == 0


def test_daily_metrics_buckets_by_day() -> None:
    sessions = [_session("t1", START, START + timedelta(hours=12))]

    metrics = daily_metrics("t1", sessions, START, START + timedelta(days=2))

    assert len(metrics) == 2
    assert metrics[0].occupied_duration == timedelta(hours=12)
    assert metrics[1].occupied_duration == timedelta(0)
