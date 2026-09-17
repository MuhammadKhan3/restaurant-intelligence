"""Table zone data model."""

from pydantic import BaseModel, field_validator


class TableZone(BaseModel):
    """A restaurant table's physical zone in the camera frame."""

    id: str
    name: str
    capacity: int
    points: list[tuple[int, int]]

    @field_validator("capacity")
    @classmethod
    def capacity_must_be_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("capacity must be at least 1")
        return value

    @field_validator("points")
    @classmethod
    def points_must_form_a_polygon(cls, value: list[tuple[int, int]]) -> list[tuple[int, int]]:
        if len(value) < 3:
            raise ValueError("a table zone needs at least 3 points to form a polygon")
        return value
