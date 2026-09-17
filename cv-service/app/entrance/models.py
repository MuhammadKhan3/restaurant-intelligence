"""Entrance zone data model: adjacent outside/inside polygons at a doorway."""

from pydantic import BaseModel, field_validator


class EntranceZone(BaseModel):
    """A doorway split into an `outside` and `inside` polygon.

    A tracked person crossing from `outside_points` to `inside_points` (or the
    reverse) between frames is what `EntranceTracker` treats as an entry/exit.
    """

    id: str
    name: str
    outside_points: list[tuple[int, int]]
    inside_points: list[tuple[int, int]]

    @field_validator("outside_points", "inside_points")
    @classmethod
    def points_must_form_a_polygon(cls, value: list[tuple[int, int]]) -> list[tuple[int, int]]:
        if len(value) < 3:
            raise ValueError("a zone needs at least 3 points to form a polygon")
        return value
