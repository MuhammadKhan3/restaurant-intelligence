"""Data models for table session analytics."""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class TableAnalytics:
    """Summary of a table's completed sessions over some period."""

    zone_id: str
    session_count: int
    average_duration: timedelta
    total_duration: timedelta
    turnover_per_day: float
    utilization: float


@dataclass(frozen=True)
class PeriodMetric:
    """Occupancy summary for a table over one fixed-size time bucket."""

    period_start: datetime
    period_end: datetime
    occupied_duration: timedelta
    session_count: int
    utilization: float
