"""Running count of customers currently inside, driven by entrance events."""

from app.entrance.tracker import EntranceEvent, EntranceEventType


class CustomerCounter:
    """Tracks the current customer count from a stream of `EntranceEvent`s.

    The count is clamped at zero: an EXIT with no corresponding prior ENTRY
    (e.g. a track first picked up already crossing out) is ignored rather than
    going negative.
    """

    def __init__(self) -> None:
        self._count = 0

    def apply(self, events: list[EntranceEvent]) -> int:
        for event in events:
            if event.event_type == EntranceEventType.ENTRY:
                self._count += 1
            elif self._count > 0:
                self._count -= 1

        return self._count

    @property
    def current_count(self) -> int:
        return self._count
