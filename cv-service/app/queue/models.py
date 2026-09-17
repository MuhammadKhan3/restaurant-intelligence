"""Queue zone data model: a single polygon where waiting customers stand."""

from pydantic import BaseModel, field_validator


class QueueZone(BaseModel):
    """The waiting area's polygon zone in the camera frame."""

    id: str
    name: str
    points: list[tuple[int, int]]

    @field_validator("points")
    @classmethod
    def points_must_form_a_polygon(cls, value: list[tuple[int, int]]) -> list[tuple[int, int]]:
        if len(value) < 3:
            raise ValueError("a queue zone needs at least 3 points to form a polygon")
        return value
