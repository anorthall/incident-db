from django.db import models

from cidb.src.core.models.generic import TimestampModel
from cidb.src.incidents.models.location import Location


class Cave(TimestampModel):
    name = models.CharField(
        default="Unknown Cave",
    )
    location = models.ForeignKey(
        Location,
        related_name="caves",
        on_delete=models.PROTECT,
    )

    class Meta:
        indexes = [
            models.Index(fields=["name"], name="incidents_cave_name"),
        ]

    def __str__(self) -> str:
        return self.name
