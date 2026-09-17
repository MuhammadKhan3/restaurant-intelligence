"""Computes table session analytics from `TableTimingTracker` session history."""

from datetime import datetime, timedelta

from app.analytics.models import PeriodMetric, TableAnalytics
from app.tables.timing import TableSession


def analyze_table(zone_id: str, sessions: list[TableSession], period: timedelta) -> TableAnalytics:
    """Summarize `zone_id`'s completed sessions over a period of length `period`.

    `period` is the span the sessions were drawn from (e.g. 24h), used to turn
    counts/durations into rates: turnover per day and fraction of time occupied.
    """
    closed = [s for s in sessions if s.zone_id == zone_id and not s.is_open]

    if not closed:
        return TableAnalytics(
            zone_id=zone_id,
            session_count=0,
            average_duration=timedelta(0),
            total_duration=timedelta(0),
            turnover_per_day=0.0,
            utilization=0.0,
        )

    durations = [session.duration() for session in closed]
    total = sum(durations, timedelta())
    average = total / len(durations)
    turnover_per_day = len(closed) / (period / timedelta(days=1)) if period > timedelta(0) else 0.0
    utilization = min(1.0, total / period) if period > timedelta(0) else 0.0

    return TableAnalytics(
        zone_id=zone_id,
        session_count=len(closed),
        average_duration=average,
        total_duration=total,
        turnover_per_day=turnover_per_day,
        utilization=utilization,
    )


def peak_occupancy(sessions: list[TableSession]) -> int:
    """The maximum number of tables occupied at the same instant, across all zones."""
    closed = [session for session in sessions if not session.is_open]
    if not closed:
        return 0

    events: list[tuple[datetime, int]] = []
    for session in closed:
        events.append((session.start_time, 1))
        events.append((session.end_time, -1))
    events.sort(key=lambda event: (event[0], event[1]))

    current = 0
    peak = 0
    for _, delta in events:
        current += delta
        peak = max(peak, current)
    return peak


def _bucket_metrics(
    zone_id: str,
    sessions: list[TableSession],
    start: datetime,
    end: datetime,
    bucket_size: timedelta,
) -> list[PeriodMetric]:
    closed = [s for s in sessions if s.zone_id == zone_id and not s.is_open]
    buckets: list[PeriodMetric] = []

    cursor = start
    while cursor < end:
        bucket_end = min(cursor + bucket_size, end)
        occupied = timedelta(0)
        count = 0

        for session in closed:
            overlap_start = max(session.start_time, cursor)
            overlap_end = min(session.end_time, bucket_end)
            if overlap_end > overlap_start:
                occupied += overlap_end - overlap_start
                count += 1

        bucket_duration = bucket_end - cursor
        utilization = occupied / bucket_duration if bucket_duration > timedelta(0) else 0.0
        buckets.append(
            PeriodMetric(
                period_start=cursor,
                period_end=bucket_end,
                occupied_duration=occupied,
                session_count=count,
                utilization=utilization,
            )
        )
        cursor = bucket_end

    return buckets


def hourly_metrics(
    zone_id: str, sessions: list[TableSession], start: datetime, end: datetime
) -> list[PeriodMetric]:
    """One `PeriodMetric` per hour between `start` and `end`."""
    return _bucket_metrics(zone_id, sessions, start, end, timedelta(hours=1))


def daily_metrics(
    zone_id: str, sessions: list[TableSession], start: datetime, end: datetime
) -> list[PeriodMetric]:
    """One `PeriodMetric` per day between `start` and `end`."""
    return _bucket_metrics(zone_id, sessions, start, end, timedelta(days=1))
