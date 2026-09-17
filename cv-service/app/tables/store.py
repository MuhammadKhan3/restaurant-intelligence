"""In-memory CRUD store for table zones, with JSON file save/load."""

import json
from pathlib import Path

from app.tables.models import TableZone


class TableZoneStore:
    """Create/edit/delete table zones, and persist them to a JSON file."""

    def __init__(self) -> None:
        self._zones: dict[str, TableZone] = {}

    def create(self, zone: TableZone) -> TableZone:
        if zone.id in self._zones:
            raise ValueError(f"Table zone already exists: {zone.id}")
        self._zones[zone.id] = zone
        return zone

    def get(self, zone_id: str) -> TableZone | None:
        return self._zones.get(zone_id)

    def list(self) -> list[TableZone]:
        return list(self._zones.values())

    def update(self, zone_id: str, zone: TableZone) -> TableZone:
        if zone_id not in self._zones:
            raise KeyError(f"Table zone not found: {zone_id}")
        if zone.id != zone_id:
            raise ValueError("zone.id must match the zone_id being updated")
        self._zones[zone_id] = zone
        return zone

    def delete(self, zone_id: str) -> None:
        if zone_id not in self._zones:
            raise KeyError(f"Table zone not found: {zone_id}")
        del self._zones[zone_id]

    def save(self, file_path: str) -> None:
        payload = [zone.model_dump() for zone in self._zones.values()]
        Path(file_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load(self, file_path: str) -> None:
        path = Path(file_path)
        if not path.exists():
            self._zones = {}
            return

        payload = json.loads(path.read_text(encoding="utf-8"))
        self._zones = {item["id"]: TableZone.model_validate(item) for item in payload}
